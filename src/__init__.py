"""
# readpub
Reader for Ebooks.

## See Also
### Github repository
* https://github.com/Chitaoji/readpub/

### PyPI project
* https://pypi.org/project/readpub/

## License
This project falls under the BSD 3-Clause License.

"""

from . import main
from .__version__ import __version__
from .main import *

__all__: list[str] = []
__all__.extend(main.__all__)
