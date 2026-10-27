"""Project-scoped files/links, served as downloads outside the static directory."""
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4
from io import BytesIO
from zipfile import ZipFile, BadZipFile
from flask import current_app
from database.connection import execute_db, query_db, transaction
from services.audit_service import log_audit
from services.validation import text, ValidationError
from services.access_service import require_active_task

ALLOWED = {'.txt','.md','.pdf','.docx','.png','.jpg','.jpeg'}
MAX_BYTES = 5 * 1024 * 1024


def storage_root():
    root = Path(current_app.config.get('UPLOAD_FOLDER', Path(current_app.instance_path) / 'uploads')).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def upload_attachment(user_id, task, file):
    require_active_task(task)
    name = text(file.filename, 'Tên tệp', 255, required=True)
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED:
        raise ValidationError('Chỉ hỗ trợ PDF, DOCX, TXT, MD, PNG, JPG.')
    data = file.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        raise ValidationError('Tệp phải có nội dung và không được vượt quá 5 MB.')
    if suffix in ('.txt','.md'):
        try:
            data.decode('utf-8-sig')
        except UnicodeDecodeError as error:
            raise ValidationError('Tệp văn bản phải dùng UTF-8.') from error
    if suffix == '.pdf' and not data.startswith(b'%PDF-'):
        raise ValidationError('Nội dung không phải tệp PDF.')
    if suffix == '.png' and not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValidationError('Nội dung không phải ảnh PNG.')
    if suffix in ('.jpg','.jpeg') and not data.startswith(b'\xff\xd8\xff'):
        raise ValidationError('Nội dung không phải ảnh JPG.')
    if suffix == '.docx':
        try:
            with ZipFile(BytesIO(data)) as archive:
                if 'word/document.xml' not in archive.namelist() or sum(item.file_size for item in archive.infolist()) > 30 * 1024 * 1024:
                    raise ValidationError('Tệp Word không hợp lệ hoặc vượt giới hạn giải nén.')
        except BadZipFile as error:
            raise ValidationError('Nội dung không phải tệp DOCX.') from error
    root = storage_root()
    target = root / (uuid4().hex + suffix)
    try:
        target.write_bytes(data)
        with transaction():
            identifier = execute_db('''INSERT INTO attachments(project_id,task_id,file_name,file_path,file_size,file_type,uploaded_by)
                VALUES (%s,%s,%s,%s,%s,%s,%s)''',
                (task['project_id'],task['id'],name,target.name,len(data),suffix[1:],user_id))
            log_audit(user_id,'UPLOAD_ATTACHMENT','ATTACHMENT',identifier,{'file_name':name,'task_id':task['id']})
        return identifier
    except BaseException:
        target.unlink(missing_ok=True)
        raise


def add_link(user_id, task, name, url):
    require_active_task(task)
    url = text(url, 'Liên kết', 500, required=True)
    parsed = urlsplit(url)
    if parsed.scheme not in ('http','https') or not parsed.netloc or parsed.username or parsed.password or any(ord(c)<32 for c in url):
        raise ValidationError('Liên kết phải là HTTP/HTTPS hợp lệ, không chứa thông tin đăng nhập.')
    name = text(name, 'Tên liên kết', 255, required=True)
    with transaction():
        identifier = execute_db('''INSERT INTO attachments(project_id,task_id,file_name,file_path,file_size,file_type,uploaded_by)
            VALUES (%s,%s,%s,%s,0,'link',%s)''', (task['project_id'],task['id'],name,url,user_id))
        log_audit(user_id,'ADD_LINK','ATTACHMENT',identifier,{'task_id':task['id']})
    return identifier


def attachment_download(identifier):
    attachment = query_db('SELECT * FROM attachments WHERE id=%s', (identifier,), one=True)
    if not attachment:
        return None, None
    if attachment['file_type'] == 'link':
        return attachment, None
    root = storage_root()
    target = (root / attachment['file_path']).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        return None, None
    return attachment, target
