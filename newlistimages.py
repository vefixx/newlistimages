import nextcord
from nextcord.ext import commands
from data.database import database
from config.config import *
from nextcord.ui import Select, View
import os

class newlistimages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_data = {}

    @nextcord.slash_command(description="Команда для выведения всех ваших картинок!")
    async def listimages(self, interaction: nextcord.Interaction):
        print(f'/newlistimages {interaction.user.id}')

        """Проверка на администратора"""

        user = await database.getUser(interaction.user.id)  # Получение пользователя
        userid = interaction.user.id
        if BLOCKEDCOMMAND_NEWLISTIMAGES == 1:
            if user[0] not in ADMINS:
                print('Не админ')
                embed = nextcord.Embed(
                    title=f'Вы не администратор.\n\n {COMMENT}',
                    color=nextcord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return 0

        """Основой блок кода"""

        all_user_images = await database.getImages(userid)  # Получаем все картинки пользователя

        # Делаем проверку на то, если нет изображений у пользователя
        if all_user_images is None:
            embed = nextcord.Embed(
                title=f'У вас нет созданных картинок.\n\nСоздайте их командой **/addimage**',
                color=nextcord.Color.dark_orange())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return 0

        # Если проверка пройдена, то продолжаем выполнение.

        # Создаем новый словарь для пользователя. В нем будет хранить выбранную картинку, чтобы ее обрабатывать.
        self.user_data[userid] = {}

        # Превращаем наши перечисления картинок в список
        images_list = []
        for image in all_user_images:
            images_list.append(image[0])    #[0] - Это имя изображения. Добавляем в список

        # Создаем View и создаем объекты для него.
        self.view_select_images = View(timeout=None)  # Задаем таймаут None, чтобы у пользователя не возникало проблем

        """Создание Select'а для выбора картинки"""
        #   Select для выбора картинки.
        self.select_images = Select(
            placeholder='Картинки',
            options=[
                nextcord.SelectOption(label=imagename, value=imagename, emoji="🖼️")
                for imagename in images_list
            ]
        )

        """Добавление Select'а для выбора картинки к View"""
        self.view_select_images.add_item(self.select_images)

        """Создание View для кнопок"""
        self.view_buttons = View(timeout=None)  # Задаем таймаут None, чтобы у пользователя не возникало проблем

        """Создание кнопок"""
        self.button_delete = nextcord.ui.Button(label="Удалить", custom_id="deleteButton",
                                                style=nextcord.ButtonStyle.red)
        self.button_unload = nextcord.ui.Button(label="Выгрузить", custom_id="unloadButton",
                                                style=nextcord.ButtonStyle.blurple)

        """Добавление кнопок к View"""
        self.view_buttons.add_item(self.button_unload)
        self.view_buttons.add_item(self.button_delete)

        """Добавление callback'ов к Select"""
        self.select_images.callback = self.callback_select_image

        """Добавление callback'ов к кнопкам"""
        self.button_delete.callback = self.callback_delete_button


        """Отправляем сообщение с нашим View где есть Select выбор картинки"""
        embed = nextcord.Embed(
            title=f'Выберите картинку/гифку',
            color=nextcord.Color.orange())

        """Информацию о премиум"""

        leftslots = user[6]
        embed.add_field(name=f"Доступных свободных мест: {leftslots}", value=f"", inline=False)
        ispremium = await database.isPremium(userid)
        if ispremium:
            timePremium = await database.getTimePremiumByUserid(userid)
            if timePremium == None:
                timePremium = 'UNLIMITED ∞'
            embed.set_footer(text=f"Premium 👑 LVL {user[3]}. Премиум закончится {timePremium}")
        else:
            embed.set_footer(text="Premium: Не активно")

        """Информацию о премиум"""

        await interaction.send(f"", view=self.view_select_images, ephemeral=True, embed=embed)




    """Callback'и для Select'ов и кнопок"""
    async def callback_select_image(self, interaction):    # callback для выбора картинки
        await interaction.response.defer()      # Чтобы не дожидаться ответа пользователя
        selected_value = interaction.data['values'][0]      # Получаем данные, которые выбрал пользователь в Select'е
        userid = interaction.user.id

        #   Задаем нашему пользователю в словаре новые данные и передаем картинку, которую он выбрал
        self.user_data[userid]['select_image'] = selected_value

        """Отправляем пользователю сообщение с кнопками (self.view_buttons) (редактируем)"""
        embed = nextcord.Embed(
            title=f'**{selected_value}**',
            color=nextcord.Color.orange())
        embed.add_field(name=f'Название: **{selected_value}**', value='', inline=False)
        embed.add_field(name=f'Дата создания: **не указана**', value='', inline=False)      # Изменить на дату создания

        #   Отправка
        await interaction.edit_original_message(content=f"", view=self.view_buttons, embed=embed)

    """Callback для кнопки"""
    async def callback_delete_button(self, interaction):
        await interaction.response.defer()  # Чтобы не дожидаться ответа пользователя
        userid = interaction.user.id

        #   Получаем изображение из даты, которое выбрал пользовать
        selected_image = self.user_data[userid]['select_image']

        """Производим процедуру удаления"""
        data = await database.delImage(name=selected_image, owner_id=interaction.user.id)


        """Процедура добавление слота"""
        #   Получаем пользователя из базы
        user = await database.getUser(userid)

        #   Получаем его кол-во оставшихся слотов
        leftImages = user[6]

        if data is not False:   # Проверка на то, удалилась ли картинка из базы или нет
            await database.setleftImages(interaction.user.id, int(leftImages) + 1)  # Добавление +1 к слоту картинок
            # Удаляем из папки картинку
            try:
                os.remove(f'data/images/{selected_image}.jpg')
            except:
                ...
            try:
                os.remove(f'data/images/{selected_image}.gif')
            except:
                ...

            """Процедура удаление этой картинки из реквестов"""

            # Берем реквесты, где есть эта картинка
            all_request_with_image = await database.getRequestsByNameImage(selected_image)

            if all_request_with_image is not None:  # Если реквесты все же есть.
                #   Перебираем и удаляем
                for request in all_request_with_image:
                    newimages = ''
                    oldimages = request[4]
                    id = request[6]
                    oldimages_split = oldimages.split(', ')
                    oldimages_split.remove(selected_image)
                    for oldimage in oldimages_split:
                        if len(newimages) == 0:
                            newimages = newimages + f'{oldimage}'
                        else:
                            newimages = newimages + f', {oldimage}'

                    await database.updateImagesInRequests(id, newimages)    # Задаем новые картинки для реквеста

            """Отправка сообщения"""
            embed = nextcord.Embed(
                title=f'Изображение/гифка (**{selected_image}**) удалено',
                color=nextcord.Color.green())
            await interaction.edit_original_message(content=f"",
                                                    embed=embed, view=None)  # Отправляем сообщение, что картинка удалена


def setup(bot: commands.Bot):
    bot.add_cog(newlistimages(bot))
