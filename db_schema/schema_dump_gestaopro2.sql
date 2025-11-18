ALTER TABLE ci_pagamento
ADD COLUMN id_pedido INTEGER;

-- Opcional, mas altamente recomendado, é adicionar a Foreign Key
ALTER TABLE ci_pagamento
ADD CONSTRAINT fk_ci_pedido
FOREIGN KEY (id_pedido)
REFERENCES pedidos(id);