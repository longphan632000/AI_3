// 3D Tilt Card and Isometric Effects Engine
document.addEventListener('DOMContentLoaded', () => {
    init3DTiltEffects();
});

function init3DTiltEffects() {
    const cards = document.querySelectorAll('.tilt-card, .kpi-card, .task-card');
    cards.forEach(card => {
        card.addEventListener('mousemove', handleCardMouseMove);
        card.addEventListener('mouseleave', handleCardMouseLeave);
    });
}

function handleCardMouseMove(e) {
    const card = e.currentTarget;
    if(card.classList.contains('task-card'))return;
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Tính toán góc nghiêng 3D (giới hạn tối đa 12 độ)
    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    const rotateX = ((y - centerY) / centerY) * -10;
    const rotateY = ((x - centerX) / centerX) * 10;
    
    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.015, 1.015, 1.015)`;
    card.style.setProperty('--mouse-x', `${(x / rect.width) * 100}%`);
    card.style.setProperty('--mouse-y', `${(y / rect.height) * 100}%`);
}

function handleCardMouseLeave(e) {
    const card = e.currentTarget;
    card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
}

// Hàm cập nhật Circular Progress Ring 3D
function updateProgressRing(percent) {
    const circle = document.querySelector('.progress-ring-circle');
    const textEl = document.querySelector('.progress-ring-percentage');
    if (!circle || !textEl) return;
    
    const radius = circle.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    const offset = circumference - (percent / 100) * circumference;
    circle.style.strokeDashoffset = offset;
    
    textEl.textContent = `${percent}%`;
}
