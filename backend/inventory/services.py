from django.db import transaction

from .models import Product, StockMovement
from .notifications import create_stock_notification


@transaction.atomic
def create_stock_movement(
    product,
    movement_type,
    quantity,
    reason='',
    reference='',
    user=None
):
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    previous_status = product.stock_status
    
    if movement_type == 'IN':
        product.quantity += quantity

    elif movement_type == 'OUT':
        if product.quantity < quantity:
            raise ValueError(
                f"Insufficient stock. Available: {product.quantity}"
            )

        product.quantity -= quantity

    elif movement_type == 'ADJUSTMENT':
        product.quantity = quantity

    else:
        raise ValueError("Invalid movement type.")

    product.save(update_fields=['quantity', 'updated_at'])

    new_status = product.stock_status

    movement = StockMovement.objects.create(
        product=product,
        movement_type=movement_type,
        quantity=quantity,
        reason=reason,
        reference=reference,
        created_by=user
    )

    create_stock_notification(
        product=product,
        previous_status=previous_status,
        new_status=new_status
    )

    return movement