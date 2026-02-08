# frozen_string_literal: true

require 'rouge'

module Rouge
  module Lexers
    class JSONiq < RegexLexer
      title 'JSONiq'
      desc 'JSONiq query language (SirixDB dialect)'
      tag 'jsoniq'
      aliases 'jq'

      keywords = %w[
        let return for in where order by ascending descending
        if then else switch case default
        some every satisfies
        try catch
        import module namespace as at
        declare variable function
        instance of cast castable treat as
        typeswitch
        not and or
        eq ne lt le gt ge
        insert delete replace rename
        into append json value of with
        at position to
        group collation
      ]

      builtins = %w[
        true false null empty
        document node element attribute text comment
        object array string integer decimal double boolean
        item
      ]

      state :root do
        # Whitespace
        rule %r/\s+/m, Text

        # Comments
        rule %r/\(:/, Comment, :comment

        # Strings
        rule %r/"/, Str::Double, :dstring
        rule %r/'/, Str::Single, :sstring

        # Predicate filter: [? ...]
        rule %r/\[\?/, Punctuation

        # Context item $$
        rule %r/\$\$/, Name::Variable::Global

        # Variables $name
        rule %r/\$[a-zA-Z_]\w*/, Name::Variable

        # Namespaced function calls: jn:open, sdb:revision, xs:dateTime, bit:array-values
        rule %r/[a-zA-Z][\w-]*:[a-zA-Z][\w-]*(?=\s*\()/, Name::Function

        # Numbers
        rule %r/\d+\.\d*([eE][+-]?\d+)?/, Num::Float
        rule %r/\.\d+([eE][+-]?\d+)?/, Num::Float
        rule %r/\d+[eE][+-]?\d+/, Num::Float
        rule %r/\d+/, Num::Integer

        # Keywords and builtins
        rule %r/[a-zA-Z_][\w-]*/ do |m|
          if keywords.include?(m[0])
            token Keyword
          elsif builtins.include?(m[0])
            token Name::Builtin
          else
            token Name
          end
        end

        # Operators and punctuation
        rule %r/:=/, Operator
        rule %r/[.]{2}/, Operator
        rule %r/[.,;:!?@#\[\](){}]/, Punctuation
        rule %r{[+\-*/=<>|]}, Operator
      end

      state :comment do
        rule %r/[^(:)]+/, Comment
        rule %r/\(:/, Comment, :comment  # nested
        rule %r/:\)/, Comment, :pop!
        rule %r/[(:)]/, Comment
      end

      state :dstring do
        rule %r/[^"]+/, Str::Double
        rule %r/""/, Str::Double
        rule %r/"/, Str::Double, :pop!
      end

      state :sstring do
        rule %r/[^']+/, Str::Single
        rule %r/''/, Str::Single
        rule %r/'/, Str::Single, :pop!
      end
    end
  end
end
