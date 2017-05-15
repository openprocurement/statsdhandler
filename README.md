[![Coverage Status](https://coveralls.io/repos/github/openprocurement/statsdhandler/badge.svg?branch=statsite_support)](https://coveralls.io/github/openprocurement/statsdhandler?branch=statsite_support)
[![Build Status](https://travis-ci.org/openprocurement/statsdhandler.svg?branch=statsite_support)](https://travis-ci.org/openprocurement/statsdhandler)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
# StatsdHandler

Logging handler для представлення параметрів, які передаються в `extra` повідомлення логування у вигляді певних метрик

Установка:

`pip install statsdhandler`
### Типи метрик

**StatsdHandler** параметри в лог записі може представляти у вигляді наступних метрик
  * **Gauge** - аплікація відправляє `metric_name:value|g` де `value` десяткове/дробове число,
  _statsd_ повертає останнє значення. Також аплікація може інкрементувати або декрементувати попереднє значення якщо перед ним першим символом буде `+` або `-`
  * **Counters/Лічильники** - аплікація відправляє `metric_name:value|c`, де `value` додатнє або від'ємне **ціле** число подій що відбулись
  _statsd_ повертає суму значень
  * **Timers/Histograms** - аплікація віправляє `metric_name:value|ms` або `metric_name:value|h`, де `value` є будь-яке дробове число,
  _statsd_ повертає **min, max, average, average of 95 percentile, median і standart deviation**
  * **Sets** - аплікація відправляє `metric_name:value|s`, де `value` будь-що (число або текст, пробіли на початку і в кінці стрічки видаляються)
  _statsd_ повертає к-ть унікальних значень серед відправлених.

### Налаштування
#### Безпосередньо в коді
```python
import logging
from statsdhandler.statsdhandler import StatsdHandler
import time

logger = logging.getLogger('mylogger')
logger.setLevel(logging.DEBUG)

sdh = StatsdHandler(config_path='path/to/config.yaml')
sdh.setLevel(logging.DEBUG)

logger.addHandler(sdh)
```

#### Використовуючи конфігураційний файл вашої аплікації
```yaml
main:
  host: localhost
  port: 1234
  my_app_other_param: some_value_3

formatters:
  simple:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: simple
    stream: ext://sys.stdout
  statsd:
    class: statsdhandler.statsdhandler.StatsdHandler
    level: DEBUG
    config_path: path/to/handler/config.yaml

loggers:
  mylogger:
    handlers: [console, statsd]
    propagate: no
    level: DEBUG

  mylogger_2:
    handlers: [console, statsd]
    propagate: no
    level: DEBUG

  "":
    handlers: [console, statsd]
    level: DEBUG
```

Лістінг конфігураційного файлу хендлера:

```yaml
main:
  app_key: app_key
  host: localhost
  port: 8125
publish_templates:
  all_levels:
    - '%(logger)s;%(attr)s;%(metric_name)s'
    - '%(attr)s;%(metric_name)s'
    - '%(metric_name)s'
  full_path:
    - '%(logger)s;%(attr)s;%(metric_name)s'
counters:
  MESSAGE_ID:
    value_type: key
  REQUEST_METHOD:
    value_equals: [POST, PUT]
    value_type: key
    publish_template: all_levels
  REQUESTS:
    value_type: value
    publish_template: full_path
timers:
  - start_attr_name: JOURNAL_REQUEST_START_1
    end_attr_name: JOURNAL_REQUEST_END_1
    publish_template: full_path
    name: timer_name
  - value_attr_name: JOURNAL_REQUEST_DUR_TIME
    publish_template: full_path
    name: timer_name_3
gauges:
  JOURNAL_GAUGE_ATTR:
    publish_template: full_path
  JOURNAL_GAUGE_ATTR_DECR: {}
histograms:
  HISTOGRAM_ARG:
    publish_template: full_path
sets:
  SET_ARG: {}
  SET_ARG:
    publish_template: full_path
```

В конфігураційному файлі хендлера ключові значення:
* секція `main`
  - `app_key` - префікс для метрик
  - `host` - ІР на якому 'крутиться' **statsd**
  - `port` - порт на якому крутиться **statsd**

* секція `publish_templates`:
  `all_levels` i `full_path` - це шаблони форматів метрик, які хендлер буде відсилати в _statsd_
  наприклад для шаблону `all_levels` і лічильника `REQUEST_METHOD` одна і таж метрика буде відсилатись тричі
  ```
  app_key.mylogger;REQUEST_METHOD;POST:1|c
  app_key.REQUEST_METHOD;POST:1|c
  app_key.POST:1|c
  ```
  такий спосіб надсилання потрібний для того щоб агрегувати одні і тіж метрики на кілької рівнях аплікації, у варіанті з логером ми отримаємо на виході к-ть POST опрацьованих певним модулем, у варіанті без логера ми отримаєм к-ть POST із заданим атрибутом по всіх логерах, і у варіанті де лише app_key i POST ми отримаємо к-ть POST по всій аплікації зі всіх модулів із різних атрибутів що відслідковуються.
* секція `counters`:
  `MESSAGE_ID`, `REQUEST_METHOD`, `REQUESTS` - перелік атрибутів `log_recod` об'єкту які будуть надсилатись в _statsd_ як лічильники, кожен з них це словник, який може бути пустим або мати наступні ключі:
  - `value_type` - це строка яка може приймати значення `key` або `value` яка вказує як інтерпретувати значення атрибуту, як ключ чи як значення, у випаду `key` значення атрибуту додасться в кінці назви метрики, а значенням лічильника буде 1
  ```python
  logger.info('Upload file', extra={'MESSAGE_ID': 'upload_file'})
  ```
  в _statsd_ відправиться наступне:
  ```
  app_key.mylogger;MESSAGE_ID;upload_file:1|c
  ```
  в іншому випадку атрибут буде закінченням назви метрики а значення атрибута буде значенням метрики
  ```python
  logger.info('New requests', extra={'REQUESTS': 5})
  ```
  в _statsd_ відправиться:
  ```
  app_key.mylogger;REQUESTS;REQUESTS:5|c
  ```
  - `value_equals` - це масив який містить значення які потрібно надсилати у _statsd_, тобто якщо атрибут `REQUEST_METHOD` матиме значення відмінне від `POST` i `PUT`, то в _statsd_ нічого не відправиться
  - `publish_template` - строка яка містить назву шаблону, якщо її не передати, то використовуватиметься шаблон по замовчуванню такий же як `full_path`, якщо передати невірну назву шаблону, то також буде використовуватись шаблон по замовчуванню.
* секція `timers`:
  Це масив словників які описують параметри таймерів:
  - `start_attr_name` - назва атрибуту, значення якого сприймати за початок відліку
  - `end_attr_name` - назва атрибуту, значення якого сприймати як кінець відліку
  - `value_attr_name` - назва атрибуту, значення якого сприймати як результат (час) виконання певного процесу
  - `name` - назва яка буде використовуватись для таймера для шаблонів це змінна `%(metric_name)s`
* секції `gauges`, `histograms` i `sets`:
  Це словники в яких ключем виступає назва атрибуту який буде представлятись як метрики `gauges`, `histograms` або `sets` в залежності від секції в якій буде розміщенний, а значенням словник який може бути пустим або містити ключ `publish_template` який вказує на шаблон форматування метрики.
