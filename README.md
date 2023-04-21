# VKinder - бот вконтакте для поиска второй половинки

## Настройка

В файле config.py установите значения для переменных

-   GROUP_TOKEN="токен группы вк"
-   USER_TOKEN="токен пользователя вк"
-   POSTGRES_URI="[что это](https://www.postgresql.org/docs/current/libpq-connect.html#id-1.7.3.8.3.6)"

Для работы бота нужны 2 токена.
Токен группы - чтобы писать от имени группы.
Токен пользователя - чтобы искать пользователей(у токена группы нет таких прав).

### Получение токена пользователя [документация вк](https://dev.vk.com/api/access-token/authcode-flow-user#%D0%9F%D0%BE%D0%BB%D1%83%D1%87%D0%B5%D0%BD%D0%B8%D0%B5%20access_token).

Перейти на https://vk.com/apps?act=manage и создать Standalone-приложение приложение получить _ID приложения_(он же client_id)

https://oauth.vk.com/authorize?client_id=51603996&display=page&redirect_uri=https://oauth.vk.com/blank.html&scope=offline,search,photos,messages&response_type=token&v=5.131&state=123456

### Установка зависимостей

```shell
pip install -r requirements.txt
```

### Запуск
```shell
python3.10 main.py
```
