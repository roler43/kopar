from aiogram.fsm.state import State, StatesGroup

class FloodStates(StatesGroup):
    waiting_for_phone = State()
    flood_active = State()

class MailingStates(StatesGroup):
    waiting_for_message = State()
