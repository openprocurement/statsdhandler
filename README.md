[![Coverage Status](https://coveralls.io/repos/github/openprocurement/statsdhandler/badge.svg)](https://coveralls.io/github/openprocurement/statsdhandler)
[![Build Status](https://travis-ci.org/openprocurement/statsdhandler.svg?branch=master)](https://travis-ci.org/openprocurement/statsdhandler)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
# StatsdHandler

Logging Handler який відслідковує задані в конфігураційному файлі `MESSAGE_ID`
і відсилає у statsite метрики які передаються в полі з префіксом `perfdata.`

### Як користуватись

```python
import logging
from statsdhandler.statsdhandler import StatsdHandler
import time

logger = logging.getLogger('logger_name')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('path_to_log.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)

sdh = StatsdHandler(config_path='path/to/config')
sdh.setLevel(logging.DEBUG)

logger.addHandler(fh)
logger.addHandler(ch)
logger.addHandler(sdh)

start = time()
logger.info('Increment counter', extra={'MESSAGE_ID': 'DOCUMENT_UPDATE',
                                        'perfdata.c.': 1})
logger.info('Increment counter with some value',
            extra={'MESSAGE_ID': 'DOCUMENT_SAVE', 'perfdata.c.': 3})
logger.info('Set dimension', extra={'MESSAGE_ID': 'INDEXATION_PROGRESS',
            'perfdata.kv.index_name': 97})
end = time()
logger.debug('Timer metric', extra={'MESSAGE_ID': 'LOGGING_DURATION',
                                    'perfdata.ms.metric_name': end - start})
```

Ключові значення в параметрі `extra`:
* `MESSAGE_ID` - має мати значення одне з таких які задані в конфіг файлі
* `perfdata.<metic_type>.<metric_name>` - це назва поля з якою працює хендлер
  складається поле:
    * `perfdata` - префікс для хендлера
    * `<metric_type>` - це тип метрики яку віддаватимемо в **statsite** може мати наступні значення
      - `kv`, `raw` - для відправлення метрик типу _<ключ>:<значення>_
      - `ms`, `h` - для відправлення таймерів
      - `c` - для відправлення лічильників
      - `g` - для відправлення _gauge_ метрик
    * `<metric_name>` - (уточнююча) назва метрики, якщо в словнику в `extra` передати 'perf-параметр' наступного формату `perfdata.MESSAGE_ID.` то замість назви метрики підставиться MESSAGE_ID в lowercase.

Лістінг конфігураційного файлу хендлера
```yaml
main:
  app_key: app_key
  host: localhost
  port: 8125
  sample_rate: 1
  disabled: False
publish_formats:
  DOCUMENT_UPDATE:
    - '%(logger)s;%(message_id)s;%(metric_name)s'
  DOCUMENT_SAVE:
    - '%(logger)s;%(message_id)s;%(metric_name)s'
  INDEXATION_PROGRESS:
    - '%(logger)s;%(message_id)s;%(metric_name)s'
  LOGGING_DURATION:
    - '%(logger)s;%(message_id)s;%(metric_name)s'
    - '%(message_id)s;%(metric_name)s'
    - '%(metric_name)s'
```
В конфігураційному файлі хендлера ключові значення:
* в секції `main`
  - `app_key` - ключ для метрик, щоб потім можна було розкинути метрики по відповідних pipe'ах
  - `host` - ІР на якому 'крутиться' **statsite**
  - `port` - порт на якому крутиться **statsite**
  повний опис [тут](https://python-statsd.readthedocs.io/en/latest/statsd.connection.html)
* в секції `publish_formats`:
  - `DOCUMENT_SAVE`, `DOCUMENT_UPDATE`, `INDEXATION_PROGRESS`, `LOGGING_DURATION` - це `MESSAGE_ID`'s які хендлер буде відсліковувати і вісилати метрики в заданих форматах
  - `'%(logger)s;%(message_id)s;%(metric_name)s'` - формат в якому будуть відіслані метрики в **statsite** наприклад при даному форматі в **statsiste** відправиться наступний рядок для таймера
`'app_key;logger_name;MESSAGE_ID;metric_name:value|ms'`
