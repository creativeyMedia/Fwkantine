// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar scroll effect
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(255, 255, 255, 0.98)';
        navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        navbar.style.boxShadow = 'none';
    }
});

// Form handling
document.getElementById('contactForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const formObject = {};
    
    // Convert FormData to object
    for (let [key, value] of formData.entries()) {
        formObject[key] = value;
    }
    
    // Show loading state
    const submitButton = this.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Wird gesendet...';
    submitButton.disabled = true;
    
    try {
        // Create email content
        const emailContent = createEmailContent(formObject);
        
        // Create mailto link
        const subject = encodeURIComponent('Canteen Manager Anfrage - ' + formObject.name);
        const body = encodeURIComponent(emailContent);
        const mailtoLink = `mailto:info@creativey.media?subject=${subject}&body=${body}`;
        
        // Open email client
        window.location.href = mailtoLink;
        
        // Show success message
        showMessage('Vielen Dank für Ihre Anfrage! Ihr E-Mail-Programm wird geöffnet.', 'success');
        
        // Reset form after short delay
        setTimeout(() => {
            this.reset();
        }, 1000);
        
    } catch (error) {
        console.error('Error:', error);
        showMessage('Entschuldigung, es gab einen Fehler. Bitte versuchen Sie es erneut oder kontaktieren Sie uns direkt.', 'error');
    } finally {
        // Reset button
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
    }
});

// Create email content
function createEmailContent(formData) {
    let content = `Neue Anfrage für Canteen Manager\n\n`;
    content += `Feuerwache: ${formData.name}\n`;
    content += `Ansprechpartner: ${formData.contact}\n`;
    content += `E-Mail: ${formData.email}\n`;
    
    if (formData.phone) {
        content += `Telefon: ${formData.phone}\n`;
    }
    
    if (formData.departments) {
        content += `Anzahl Wachabteilungen: ${formData.departments}\n`;
    }
    
    content += `\nNachricht:\n${formData.message || 'Keine spezifische Nachricht'}\n\n`;
    content += `---\n`;
    content += `Diese Anfrage wurde über die Canteen Manager Landing Page gesendet.\n`;
    content += `Datum: ${new Date().toLocaleDateString('de-DE')}\n`;
    content += `Uhrzeit: ${new Date().toLocaleTimeString('de-DE')}`;
    
    return content;
}

// Show success/error messages
function showMessage(message, type) {
    // Remove existing messages
    const existingMessages = document.querySelectorAll('.success-message, .error-message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = type === 'success' ? 'success-message' : 'error-message';
    messageDiv.textContent = message;
    
    // Insert after form
    const form = document.getElementById('contactForm');
    form.parentNode.insertBefore(messageDiv, form.nextSibling);
    
    // Remove message after 5 seconds
    setTimeout(() => {
        messageDiv.remove();
    }, 5000);
}

// Animate elements on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-fadeInUp');
        }
    });
}, observerOptions);

// Observe elements for animation
document.addEventListener('DOMContentLoaded', () => {
    const animateElements = document.querySelectorAll('.feature-card, .screenshot-item, .benefit-item, .stat-big');
    animateElements.forEach(el => observer.observe(el));
});

// App window interaction
document.addEventListener('DOMContentLoaded', () => {
    const appWindow = document.querySelector('.app-window');
    if (appWindow) {
        appWindow.addEventListener('mouseenter', () => {
            appWindow.style.transform = 'rotateY(0deg) rotateX(0deg) scale(1.02)';
        });
        
        appWindow.addEventListener('mouseleave', () => {
            appWindow.style.transform = 'rotateY(-5deg) rotateX(5deg) scale(1)';
        });
    }
});

// Statistics counter animation
function animateCounter(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const current = Math.floor(progress * (end - start) + start);
        element.textContent = current + (end === 100 ? '%' : '');
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Animate counters when they come into view
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const statNumber = entry.target.querySelector('.stat-number');
            const targetNumber = parseInt(statNumber.textContent);
            
            if (targetNumber === 100) {
                animateCounter(statNumber, 0, 100, 2000);
            } else if (targetNumber === 24) {
                // For "24/7", just animate the "24" part
                statNumber.textContent = '24/7';
            } else if (targetNumber === 0) {
                // For "0€", animate from higher number down
                animateCounter(statNumber, 1000, 0, 2000);
                setTimeout(() => {
                    statNumber.textContent = '0€';
                }, 2000);
            }
            
            statsObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

document.addEventListener('DOMContentLoaded', () => {
    const statBigs = document.querySelectorAll('.stat-big');
    statBigs.forEach(stat => statsObserver.observe(stat));
});

// Mobile menu toggle (if needed)
function toggleMobileMenu() {
    const navLinks = document.querySelector('.nav-links');
    navLinks.classList.toggle('active');
}

// Handle form field interactions
document.addEventListener('DOMContentLoaded', () => {
    const formInputs = document.querySelectorAll('.form-group input, .form-group select, .form-group textarea');
    
    formInputs.forEach(input => {
        input.addEventListener('focus', (e) => {
            e.target.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', (e) => {
            e.target.parentElement.classList.remove('focused');
            if (e.target.value) {
                e.target.parentElement.classList.add('filled');
            } else {
                e.target.parentElement.classList.remove('filled');
            }
        });
    });
});

// Parallax effect for hero section
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const parallaxElement = document.querySelector('.hero-image');
    
    if (parallaxElement && scrolled < window.innerHeight) {
        const speed = scrolled * 0.5;
        parallaxElement.style.transform = `translateY(${speed}px)`;
    }
});

// Dynamic typing effect for hero title (optional)
function typeWriter(element, text, speed = 100) {
    let i = 0;
    element.innerHTML = '';
    
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    
    type();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Add any initialization code here
    console.log('Canteen Manager Landing Page loaded successfully!');
    
    // Preload critical images
    const criticalImages = [
        'screenshot-dashboard.jpg',
        'screenshot-order.jpg',
        'screenshot-history.jpg',
        'screenshot-mobile.jpg'
    ];
    
    criticalImages.forEach(src => {
        const img = new Image();
        img.src = src;
    });
});

// Easter egg: Konami code
let konamiCode = [];
const konamiSequence = [
    'ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown',
    'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight',
    'KeyB', 'KeyA'
];

document.addEventListener('keydown', (e) => {
    konamiCode.push(e.code);
    
    if (konamiCode.length > konamiSequence.length) {
        konamiCode.shift();
    }
    
    if (konamiCode.length === konamiSequence.length && 
        konamiCode.every((code, index) => code === konamiSequence[index])) {
        // Easter egg triggered
        document.body.style.animation = 'rainbow 2s linear infinite';
        setTimeout(() => {
            document.body.style.animation = '';
        }, 5000);
        
        konamiCode = [];
    }
});

// Add rainbow animation for easter egg
const style = document.createElement('style');
style.textContent = `
    @keyframes rainbow {
        0% { filter: hue-rotate(0deg); }
        100% { filter: hue-rotate(360deg); }
    }
`;
document.head.appendChild(style);