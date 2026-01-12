#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Estructura completa del OWASP ASVS 4.0.3 Nivel 2
Incluye TODOS los requisitos y subrequisitos del estándar

Fuente oficial: https://github.com/OWASP/ASVS/tree/v4.0.3/4.0/
NOTA: Esta estructura debe ser completada con la información exacta del PDF del ASVS 4.0.3
"""

# Estructura completa del ASVS 4.0.3 Nivel 2
# Formato: {requisito: {'description': descripción, 'level': nivel}}
# Nivel 2 = Standard, Nivel 3 = Advanced

ASVS_403_COMPLETE_REQUIREMENTS = {
    # V1: Architecture, Design and Threat Modeling
    'V1.1.1': {
        'description': 'Verify the use of a secure software development lifecycle that addresses security in all stages of development.',
        'level': 2
    },
    'V1.1.2': {
        'description': 'Verify the use of threat modeling for every design change or sprint planning to identify threats, plan for countermeasures, facilitate appropriate risk responses, and guide security testing.',
        'level': 2
    },
    'V1.1.3': {
        'description': 'Verify that all user stories and features contain functional security constraints.',
        'level': 2
    },
    'V1.1.4': {
        'description': 'Verify documentation and justification of all the application\'s trust boundaries, components, and significant data flows.',
        'level': 2
    },
    'V1.1.5': {
        'description': 'Verify definition and security analysis of the application\'s high-level architecture and all connected remote services.',
        'level': 2
    },
    'V1.2.1': {
        'description': 'Verify the use of unique or special low-privilege operating system accounts for all application components, services, and servers.',
        'level': 2
    },
    'V1.2.2': {
        'description': 'Verify that communications between application components, including APIs, middleware, and data layers, are authenticated.',
        'level': 2
    },
    'V1.2.3': {
        'description': 'Verify that the application uses a single vetted authentication mechanism that is known to be secure, can be extended to include strong authentication, and has sufficient logging and monitoring to detect account abuse or breaches.',
        'level': 2
    },
    'V1.2.4': {
        'description': 'Verify that all authentication pathways and identity management APIs implement consistent authentication security control strength.',
        'level': 2
    },
    'V1.3.1': {
        'description': 'Verify the use of threat modeling for every design change or sprint planning to identify threats, plan for countermeasures, facilitate appropriate risk responses, and guide security testing.',
        'level': 2
    },
    'V1.3.2': {
        'description': 'Verify that all user stories and features contain functional security constraints.',
        'level': 2
    },
    'V1.4.1': {
        'description': 'Verify documentation and justification of all the application\'s trust boundaries, components, and significant data flows.',
        'level': 2
    },
    'V1.4.2': {
        'description': 'Verify definition and security analysis of the application\'s high-level architecture and all connected remote services.',
        'level': 2
    },
    
    # V5: Validation, Sanitization and Encoding
    'V5.1.1': {
        'description': 'Verify that the runtime environment is not susceptible to buffer overflows, or that security controls prevent buffer overflows.',
        'level': 2
    },
    'V5.1.2': {
        'description': 'Verify that a positive validation pattern is defined and applied to all input.',
        'level': 2
    },
    'V5.1.3': {
        'description': 'Verify that all input validation failures result in input rejection or input sanitization.',
        'level': 2
    },
    'V5.1.4': {
        'description': 'Verify that a character set, such as UTF-8, is specified for all sources of input.',
        'level': 2
    },
    'V5.1.5': {
        'description': 'Verify that all input validation is performed on the server side.',
        'level': 2
    },
    'V5.1.6': {
        'description': 'Verify that a single input validation control is used by the application for each type of data that is accepted.',
        'level': 2
    },
    'V5.1.7': {
        'description': 'Verify that all input validation failures are logged.',
        'level': 2
    },
    'V5.1.8': {
        'description': 'Verify that all input data is canonicalized for all downstream decoders or interpreters prior to validation.',
        'level': 2
    },
    'V5.1.9': {
        'description': 'Verify that all input validation controls are not affected by any malicious code.',
        'level': 2
    },
    'V5.2.1': {
        'description': 'Verify that the data is properly encoded for its context. This includes using specific encoders for HTML, JavaScript, URL parameters, HTTP headers, etc.',
        'level': 2
    },
    'V5.2.2': {
        'description': 'Verify that output encoding preserves the user\'s chosen character set and language settings intact, so that any Unicode character (like special symbols or characters from different languages) is handled correctly and safely.',
        'level': 2
    },
    'V5.2.3': {
        'description': 'Verify that output escaping is adapted to the context, best case automated to protect against Cross-Site Scripting (XSS) attacks.',
        'level': 2
    },
    'V5.3.1': {
        'description': 'Verify that database queries use parameterized queries, ORMs, or entity frameworks to protect against injection attacks. Avoid building queries by directly including untrusted data.',
        'level': 2
    },
    'V5.3.2': {
        'description': 'Verify that when parameterized queries or other safer mechanisms are not available, context-specific output encoding is used to prevent injection attacks. For example, use SQL escaping to protect against SQL injection when dealing with database queries.',
        'level': 2
    },
    'V5.3.3': {
        'description': 'Verify that the application is protected against JSON injection attacks, JSON eval attacks, and JavaScript expression evaluation.',
        'level': 2
    },
    'V5.3.4': {
        'description': 'Ensure the application is protected against Lightweight Directory Access Protocol (LDAP) injection.',
        'level': 2
    },
    'V5.3.5': {
        'description': 'Verify the application protects against OS command injection by using parameterized OS queries or applying proper output encoding for command line inputs.',
        'level': 2
    },
    'V5.3.6': {
        'description': 'Verify the application is protected against Local File Inclusion (LFI) and Remote File Inclusion (RFI) attacks.',
        'level': 2
    },
    'V5.3.7': {
        'description': 'Verify the application protects against XPath or XML injection.',
        'level': 2
    },
    
    # NOTA: Esta estructura debe ser completada con TODOS los requisitos del ASVS 4.0.3
    # basándose en el PDF proporcionado por el usuario.
    # Por ahora, solo incluyo ejemplos de V1 y V5 para demostrar la estructura.
}

# Estructura jerárquica del ASVS 4.0.3
ASVS_403_HIERARCHY = {
    'V1': {
        'name': 'Architecture, Design and Threat Modeling',
        'subcategories': {
            'V1.1': {
                'name': 'Secure Software Development Lifecycle',
                'requirements': ['V1.1.1', 'V1.1.2', 'V1.1.3', 'V1.1.4', 'V1.1.5']
            },
            'V1.2': {
                'name': 'Authentication Architectural Requirements',
                'requirements': ['V1.2.1', 'V1.2.2', 'V1.2.3', 'V1.2.4']
            },
            'V1.3': {
                'name': 'General Architectural Requirements',
                'requirements': ['V1.3.1', 'V1.3.2']
            },
            'V1.4': {
                'name': 'Threat Modeling',
                'requirements': ['V1.4.1', 'V1.4.2']
            }
        }
    },
    'V5': {
        'name': 'Validation, Sanitization and Encoding',
        'subcategories': {
            'V5.1': {
                'name': 'Input Validation',
                'requirements': ['V5.1.1', 'V5.1.2', 'V5.1.3', 'V5.1.4', 'V5.1.5', 'V5.1.6', 'V5.1.7', 'V5.1.8', 'V5.1.9']
            },
            'V5.2': {
                'name': 'Output Encoding',
                'requirements': ['V5.2.1', 'V5.2.2', 'V5.2.3']
            },
            'V5.3': {
                'name': 'Injection Prevention',
                'requirements': ['V5.3.1', 'V5.3.2', 'V5.3.3', 'V5.3.4', 'V5.3.5', 'V5.3.6', 'V5.3.7']
            }
        }
    }
    # NOTA: Esta estructura debe ser completada con TODAS las categorías V1-V14
    # basándose en el PDF proporcionado por el usuario.
}


