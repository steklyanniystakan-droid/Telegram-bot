import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

BOT_TOKEN = "8976855126:AAEscnh6NiVECzTXEt-_60NnEX7v5JHhA6U"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

class CalcStates(StatesGroup):
    waiting_for_material = State()
    waiting_for_length = State()
    waiting_for_section = State()

def calculate_ik(material: str, length: float, section: float) -> float:
    rho = 0.0175 if material == 'Медь' else 0.0281
    voltage = 230.0
    resistance = 2 * rho * (length / section)
    if resistance == 0:
        return 0.0
    ik = voltage / resistance
    return round(ik, 2)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Медь", callback_data="mat_copper"),
            InlineKeyboardButton(text="Алюминий", callback_data="mat_aluminum")
        ]
    ])
    await message.answer("Привет! Я инженерный бот для расчета токов КЗ.\nВыберите материал проводника:", reply_markup=keyboard)
    await state.set_state(CalcStates.waiting_for_material)

@router.callback_query(CalcStates.waiting_for_material, F.data.startswith("mat_"))
async def process_material(callback: CallbackQuery, state: FSMContext):
    material = "Медь" if callback.data == "mat_copper" else "Алюминий"
    await state.update_data(material=material)
    await callback.answer() 
    await callback.message.edit_text(f"Материал выбран: {material}")
    await callback.message.answer("Введите длину кабельной трассы в метрах (например, 6000):")
    await state.set_state(CalcStates.waiting_for_length)

@router.message(CalcStates.waiting_for_length)
async def process_length(message: Message, state: FSMContext):
    try:
        length = float(message.text.replace(',', '.'))
        if length <= 0:
            raise ValueError
        await state.update_data(length=length)
        await message.answer("Введите сечение кабеля в мм² (например, 120):")
        await state.set_state(CalcStates.waiting_for_section)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное положительное число для длины.")

@router.message(CalcStates.waiting_for_section)
async def process_section(message: Message, state: FSMContext):
    try:
        section = float(message.text.replace(',', '.'))
        if section <= 0:
            raise ValueError
        user_data = await state.get_data()
        material = user_data['material']
        length = user_data['length']
        ik = calculate_ik(material, length, section)
        result_text = f"Результат расчета:\nМатериал: {material}\nДлина: {length} м\nСечение: {section} мм²\n\nТок короткого замыкания: {ik} А\n\nЧтобы начать новый расчет, нажмите /start"
        await message.answer(result_text)
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное положительное число для сечения.")

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
