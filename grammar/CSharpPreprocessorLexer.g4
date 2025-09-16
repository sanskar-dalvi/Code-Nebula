lexer grammar CSharpPreprocessorLexer;

channels { COMMENTS_CHANNEL, DIRECTIVE_CHANNEL }

DIRECTIVE_NEW_LINE
    :   DIRECTIVE_NEW_LINE_PREAMBLE ('\u0000' | '\u0001' | ~[\r\n\u0000\u0001])*
        -> channel(DIRECTIVE_CHANNEL)
    ;

DIRECTIVE_NEW_LINE_PREAMBLE
    :   '#' WHITESPACE? (define | undef | if | elif | else | endif | line | error | warning | region | endregion | pragma) WHITESPACE
    ;

DEFINE
    :   '#' WHITESPACE? 'define' WHITESPACE ID
        -> channel(DIRECTIVE_CHANNEL)
    ;

UNDEF
    :   '#' WHITESPACE? 'undef' WHITESPACE ID
        -> channel(DIRECTIVE_CHANNEL)
    ;

ELIF
    :   '#' WHITESPACE? 'elif' WHITESPACE
        -> channel(DIRECTIVE_CHANNEL)
    ;

ENDIF
    :   '#' WHITESPACE? 'endif'
        -> channel(DIRECTIVE_CHANNEL)
    ;

LINE
    :   '#' WHITESPACE? 'line' WHITESPACE
        -> channel(DIRECTIVE_CHANNEL)
    ;

ERROR
    :   '#' WHITESPACE? 'error' WHITESPACE
        -> channel(DIRECTIVE_CHANNEL)
    ;

WARNING
    :   '#' WHITESPACE? 'warning' WHITESPACE
        -> channel(DIRECTIVE_CHANNEL)
    ;

REGION
    :   '#' WHITESPACE? 'region' WHITESPACE
        -> channel(DIRECTIVE_CHANNEL)
    ;

ENDREGION
    :   '#' WHITESPACE? 'endregion'
        -> channel(DIRECTIVE_CHANNEL)
    ;

PRAGMA
    :   '#' WHITESPACE? 'pragma' WHITESPACE
        -> channel(DIRECTIVE_CHANNEL)
    ;

true
    :   'true'
    ;

false
    :   'false'
    ;

conditionalSymbol
    :   ID
    ;

ID
    :   IdentifierStartCharacter IdentifierPartCharacter*
    ;

fragment IdentifierStartCharacter
    :   [a-zA-Z_]
    ;

fragment IdentifierPartCharacter
    :   [a-zA-Z_0-9]
    ;

WHITESPACE
    :   [ \t]+ -> channel(HIDDEN)
    ;

NEW_LINE
    :   ('\r\n' | '\r' | '\n') -> channel(HIDDEN)
    ;

BLOCK_COMMENT
    :   '/*' .*? '*/' -> channel(COMMENTS_CHANNEL)
    ;

LINE_COMMENT
    :   '//' ~[\r\n]* -> channel(COMMENTS_CHANNEL)
    ;
