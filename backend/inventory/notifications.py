from django.contrib.auth.models import User

from .models import Notification


def create_stock_notification(
    product,
    previous_status,
    new_status,
    movement_type=None,
    quantity=None,
    user=None,
):
    """
    Create a notification when a product transitions
    into LOW_STOCK or OUT_OF_STOCK.
    """
    users = list(User.objects.filter(
        profile__role__in=['ADMIN', 'MANAGER']
    ))
    if user and user.is_authenticated and user not in users:
        users.append(user)

    if movement_type:
        movement_labels = {
            'IN': 'Stock in completed',
            'OUT': 'Stock out completed',
            'ADJUSTMENT': 'Stock adjustment completed',
        }
        movement_label = movement_labels[movement_type]
        movement_message = (
            f'{movement_label} for {product.name}: {quantity} units processed. '
            f'Current quantity: {product.quantity}.'
        )
        for user in users:
            Notification.objects.create(
                user=user,
                product=product,
                title=movement_label,
                message=movement_message,
                notification_type='STOCK_MOVEMENT',
            )

    if previous_status == new_status:
        return

    if new_status == 'LOW_STOCK':
        notification_type = 'LOW_STOCK'
        title = 'Low Stock Alert'
        message = (
            f'{product.name} is low on stock. '
            f'Current quantity: {product.quantity}. '
            f'Minimum stock: {product.minimum_stock}.'
        )

    elif new_status == 'OUT_OF_STOCK':
        notification_type = 'OUT_OF_STOCK'
        title = 'Out of Stock Alert'
        message = f'{product.name} is out of stock.'

    else:
        return

    for user in users:
        Notification.objects.create(
            user=user,
            product=product,
            title=title,
            message=message,
            notification_type=notification_type,
        )

