import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.routers.pedido_router import create_pedido
from app.schemas.pedido_schema import PedidoCreateRequest
from decimal import Decimal

def test_create_pedido_saldo_error_returns_400():
    req = PedidoCreateRequest(item_contrato_id=1, quantidade_pedida=Decimal("100"))
    
    with patch("app.routers.pedido_router.PedidoRepository") as MockRepo:
        MockRepo.return_value.create.side_effect = ValueError("Saldo insuficiente")
        
        with pytest.raises(HTTPException) as exc:
            create_pedido(1, req, MagicMock(), MagicMock())
        
        assert exc.value.status_code == 400
        assert "Saldo insuficiente" in str(exc.value.detail)
        print("\n[Pedido Router] PASSOU: Erro de saldo virou 400.")