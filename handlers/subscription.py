from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards import get_main_keyboard
from config import CHANNEL_USERNAME
from emojis import Emojis

router = Router()

@router.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    try:
        chat_member = await callback.bot.get_chat_member(
            chat_id=f"@{CHANNEL_USERNAME}",
            user_id=user_id
        )
        
        if chat_member.status not in ['left', 'kicked']:
            try:
                await callback.message.delete()
            except:
                pass
            
            await callback.message.answer(
                f"{Emojis.SUCCESS} <b>Подписка подтверждена!</b>\n\n"
                f"Добро пожаловать в главное меню.",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
        else:
            await callback.answer(f"{Emojis.ERROR} Вы не подписаны на канал!", show_alert=True)
    except:
        await callback.answer(f"{Emojis.ERROR} Ошибка при проверке подписки!", show_alert=True)
    
    await callback.answer()
