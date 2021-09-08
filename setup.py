from setuptools import setup, find_packages

setup_requires = [
      ]

install_requires = [
      'numpy>=1.17.0',
      'pandas>=1.0.5',
      'tqdm>=4.47.0',
      'matplotlib>=3.3.3',
      'mplfinance>=0.12.7a5',
      'mysqlclient>=1.4.6',
      'QtPy>=1.9.0',
      'SQLAlchemy>=1.3.18',
      'requests>=2.24.0',
      'beautifulsoup4>=4.9.1',
      ]

setup(name='ko-stock-assistant',
      version='1.0',
      url='https://github.com/sanggong/ko-stock-assistant',
      license='MIT',
      author='sanggong',
      author_email='gndlmbs@naver.com',
      description='Assist Korean stock market trading',
      packages=find_packages(),
      install_requires=install_requires,
      setup_requires=setup_requires,
      classifiers=[],  # check!
      long_description=open('README.md').read(),
      zip_safe=False, # check!
      test_suite='nose.collector') # check!