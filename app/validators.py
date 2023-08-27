from wtforms.validators import Regexp
import re

YMD_ERROR_MESSAGE = 'Enter date in YYYY-MM-DD format, like 2023-08-23'
YM_ERROR_MESSAGE  = 'Enter date in YYYY-MM format, like 2023-08'
YM_REGEX          = re.compile(r'^(19[789]|20[0-4])\d-(0[1-9]|1[0-2])$')
YMD_REGEX         = re.compile(r'^(19[789]|20[0-4])\d-(0[1-9]|1[0-2])-(30|31|0[1-9]|[12]\d)$')

class ISOYearMonthValidator(Regexp):

    def __init__(self, message=YM_ERROR_MESSAGE):
        super().__init__(regex=YM_REGEX, message=message)

class ISOYearMonthDayValidator(Regexp):

    def __init__(self, message=YMD_ERROR_MESSAGE):
        super().__init__(regex=YMD_REGEX, message=message)
