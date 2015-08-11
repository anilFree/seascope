Seascope supports various backends using plugins.

# Backend Plugins #
  * [CscopePlugin](CscopePlugin.md)
    * cscope supports C, lex, yacc files. C++ and Java support is limited
  * [IdutilsPlugin](IdutilsPlugin.md)
    * supports all languages supported by ctags like C, C++, Java, Python ...
    * For custom/new language
      * Use [ctags regex configuration](http://ctags.sourceforge.net/EXTENDING.html) to help generate ctags
      * Use [idutils langugage map](http://www.gnu.org/s/idutils/manual/idutils.html#Language-map) to enable idutils parsing of file
  * [GtagsPlugin](GtagsPlugin.md)
    * supports C, C++, Yacc, Java, PHP


# Choosing a backend #
  * C, C++, Java: Use any of the backends and see which one works better for you
  * Python: Use idutils backend
  * Mix of several languages: Use idutils backend