# Como contribuir

Valor diferente do esperado ou caso de borda que falta: abra uma issue pelo
modelo "Valor diferente do esperado". Para mandar código:

- Os testes rodam do checkout, sem instalar nada (Python 3.9 ou mais novo):

  ```bash
  python -m unittest
  ```

- Só a biblioteca padrão: nenhuma dependência.
- `Decimal` em toda conta; `float` não entra.
- Todo valor de tabela tem ao lado a fonte legal e a data em que foi lido
  (`simples_nacional/tabelas.py`). Valor sem fonte não entra.
- Todo caso novo tem teste com a conta feita à mão no próprio teste, e as
  fronteiras (o teto da faixa e um centavo acima) também.
- Exemplos e testes com números inventados: nada de dado real de empresa.
- Código, mensagens e documentação em português do Brasil.
- Mudança de comportamento entra no [CHANGELOG.md](CHANGELOG.md).
- Código próprio: não traga código copiado de outro projeto, mesmo de
  licença livre. O que você contribui sai sob a [licença MIT](LICENSE) do
  projeto.
