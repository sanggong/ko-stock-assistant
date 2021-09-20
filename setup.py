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
      'pyqt5>=5.15.4',
      'SQLAlchemy>=1.3.18',
      'requests>=2.24.0',
      'beautifulsoup4>=4.9.1',
      'pywinauto>=0.6.8'
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
      python_requires='=3.6',
      classifiers=[
            'Operating System :: Microsoft :: Windows',
            'Programming Language :: Python :: 3.6',
      ],
      long_description=open('README.md').read(),
      zip_safe=False)