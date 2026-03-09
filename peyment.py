from aiocryptopay import AioCryptoPay, Networks
from config import CRYPTO_TOKEN, PRICES, SUBSCRIPTION_DURATION
from database import db

crypto = AioCryptoPay(token=CRYPTO_TOKEN, network=Networks.MAIN_NET)

async def create_payment(user_id: int, subscription_type: str, currency: str = 'USDT'):
    """Создание платежа"""
    amount = PRICES.get(subscription_type, 1.0)
    
    # Названия подписок для отображения
    sub_names = {
        '1day': '1 день',
        '7days': '7 дней',
        '30days': '30 дней',
        'forever': 'Навсегда'
    }
    
    try:
        invoice = await crypto.create_invoice(
            asset=currency, 
            amount=amount,
            description=f"VIP подписка {sub_names[subscription_type]}"
        )
        
        # Сохраняем в базу
        db.add_payment(
            user_id=user_id,
            invoice_id=invoice.invoice_id,
            amount=amount,
            currency=currency,
            subscription_type=subscription_type
        )
        
        return {
            'success': True,
            'invoice_id': invoice.invoice_id,
            'pay_url': invoice.bot_invoice_url,
            'amount': amount,
            'currency': currency
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def check_payment(invoice_id: str):
    """Проверка статуса платежа"""
    try:
        invoices = await crypto.get_invoices(invoice_ids=invoice_id)
        if invoices:
            invoice = invoices[0]
            db.update_payment_status(invoice_id, invoice.status)
            
            return {
                'success': True,
                'status': invoice.status,
                'amount': invoice.amount
            }
    except Exception as e:
        print(f"Payment error: {e}")
    
    return {'success': False, 'status': 'unknown'}

def get_subscription_keyboard():
    """Клавиатура с подписками"""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🌟 1 день - 0.10$", callback_data="buy_1day"))
    builder.add(InlineKeyboardButton(text="✨ 7 дней - 1.00$", callback_data="buy_7days"))
    builder.add(InlineKeyboardButton(text="💫 30 дней - 4.00$", callback_data="buy_30days"))
    builder.add(InlineKeyboardButton(text="👑 Навсегда - 8.00$", callback_data="buy_forever"))
    builder.add(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_profile"))
    builder.adjust(1)
    return builder.as_markup()
