from services.gemini_service import GeminiService
from services.gemini_service import AIProviderError
from services.kira_service import KiraAIService
from services.ai_config import resolve_ai_setting

class AIProviderService:
    """
    Lớp điều phối nhà cung cấp AI (NFR-07, NFR-11).
    Cho phép thay đổi nhà cung cấp (Kira AI, Gemini, OpenAI...) mà không ảnh hưởng tới core logic.
    """
    def __init__(self, provider_name=None):
        if provider_name is None:
            self.provider_name = resolve_ai_setting('AI_PROVIDER', 'gemini')[0].lower()
        else:
            self.provider_name = provider_name.lower()

        if self.provider_name in ('kira', 'qwen', 'openai'):
            self.provider = KiraAIService()
        elif self.provider_name == 'gemini':
            self.provider = GeminiService()
        else:
            raise AIProviderError(f'Nhà cung cấp AI "{self.provider_name}" chưa được hỗ trợ.')
            
    def generate_response(self, prompt_text, max_output_tokens=4096, json_output=False):
        return self.provider.generate_content(prompt_text, max_output_tokens=max_output_tokens,
                                              json_output=json_output)
