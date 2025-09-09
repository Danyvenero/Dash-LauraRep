// Script para forçar cores corretas nos dropdowns
// Dashboard Laura Representações

document.addEventListener('DOMContentLoaded', function() {
    console.log('🎨 Iniciando correção de cores dos dropdowns...');
    
    // Função para aplicar cores corretas
    function fixDropdownColors() {
        // Selecionar todos os elementos de opções de dropdown
        const selectors = [
            '.Select-option',
            '[role="option"]',
            '.dropdown-item',
            '.Select-menu div',
            '.Select-menu-outer div',
            '[class*="option"]',
            '[class*="Option"]'
        ];
        
        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                // Força cor do texto
                element.style.setProperty('color', '#000000', 'important');
                element.style.setProperty('background-color', 'white', 'important');
                
                // Adiciona event listeners para manter as cores
                element.addEventListener('mouseenter', function() {
                    this.style.setProperty('background-color', '#0066cc', 'important');
                    this.style.setProperty('color', 'white', 'important');
                });
                
                element.addEventListener('mouseleave', function() {
                    if (!this.classList.contains('is-selected')) {
                        this.style.setProperty('background-color', 'white', 'important');
                        this.style.setProperty('color', '#000000', 'important');
                    }
                });
            });
        });
        
        console.log(`🎨 Aplicado correção de cor em ${document.querySelectorAll(selectors.join(',')).length} elementos`);
    }
    
    // Executa imediatamente
    fixDropdownColors();
    
    // Observer para detectar novos dropdowns criados dinamicamente
    const observer = new MutationObserver(function(mutations) {
        let shouldFix = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        // Verifica se é um dropdown ou contém dropdown
                        if (node.classList && (
                            node.classList.contains('Select-menu') ||
                            node.classList.contains('Select-menu-outer') ||
                            node.querySelector('.Select-option') ||
                            node.querySelector('[role="option"]')
                        )) {
                            shouldFix = true;
                        }
                    }
                });
            }
        });
        
        if (shouldFix) {
            setTimeout(fixDropdownColors, 100); // Pequeno delay para garantir renderização
        }
    });
    
    // Observa mudanças no DOM
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Executa periodicamente como fallback
    setInterval(fixDropdownColors, 2000);
    
    console.log('✅ Sistema de correção de cores dos dropdowns ativo');
});

// Função global para forçar correção manual
window.fixDropdownColors = function() {
    console.log('🔧 Forçando correção manual de cores...');
    
    // Força estilos em todos os elementos possíveis
    const allElements = document.querySelectorAll('*');
    allElements.forEach(element => {
        const computedStyle = window.getComputedStyle(element);
        const parentClasses = element.parentElement ? element.parentElement.className : '';
        
        // Se está dentro de um dropdown e tem cor clara
        if ((parentClasses.includes('Select-menu') || 
             parentClasses.includes('dropdown') ||
             element.getAttribute('role') === 'option' ||
             element.className.includes('option')) &&
            (computedStyle.color === 'rgb(255, 255, 255)' || 
             computedStyle.color === 'rgba(255, 255, 255, 1)' ||
             computedStyle.color === 'white')) {
            
            element.style.setProperty('color', '#000000', 'important');
            element.style.setProperty('background-color', 'white', 'important');
            console.log('🎨 Corrigido elemento:', element);
        }
    });
};
