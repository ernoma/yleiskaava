
class QgsPluginException(Exception):
    """ Use this as a base exception class in custom exceptions """

class QaavaDatabaseNotSetException(QgsPluginException):
    pass


class QaavaAuthConfigException(QgsPluginException):
    pass
