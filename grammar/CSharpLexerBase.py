from antlr4 import Lexer

class CSharpLexerBase(Lexer):

    def __init__(self, input_stream):
        super().__init__(input_stream)

    def CheckPreviousTokenText(self, text):
        stream = self._input
        index = stream.index
        if index < len(text):
            return False
        if stream.getText(index - len(text), index - 1) == text:
            return True
        return False

    def IsNewLine(self, _symbol):
        return _symbol.text == "\n" or _symbol.text == "\r"

    def IsValidUnicode(self, codepoint):
        return (
            codepoint == 0x0000
            or codepoint == 0x0009
            or codepoint == 0x000B
            or codepoint == 0x000C
            or codepoint == 0x000D
            or (0x0020 <= codepoint <= 0x007E)
            or (0x00A0 <= codepoint <= 0x00FF)
            or (0x0100 <= codepoint <= 0xFFFD)
            or (0x10000 <= codepoint <= 0x10FFFF)
        )

    def IsIdentifierStartCharacter(self, codepoint):
        return self.IsValidUnicode(codepoint) and (
            codepoint == 0x005F
            or (0x0041 <= codepoint <= 0x005A)
            or (0x0061 <= codepoint <= 0x007A)
        )

    def IsIdentifierPartCharacter(self, codepoint):
        return self.IsIdentifierStartCharacter(codepoint) or (
            codepoint == 0x0030
            or codepoint == 0x0031
            or codepoint == 0x0032
            or codepoint == 0x0033
            or codepoint == 0x0034
            or codepoint == 0x0035
            or codepoint == 0x0036
            or codepoint == 0x0037
            or codepoint == 0x0038
            or codepoint == 0x0039
        )
