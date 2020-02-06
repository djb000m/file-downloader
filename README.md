# File Downloader

A little tool to download all files of a specified type from a supplied url.

The script is a little raw. It needs a better menu, the code needs improving and, at this point, there aren't any saftey checks - there is a possibility that you start downloading a ridiculous amount of large files without prior warning.

Having said all that, it works. To horrendously misquote Ordell Robbie in [Jackie Brown](https://www.imdb.com/title/tt0119396/?ref_=fn_al_tt_1):

> "When you absolutely, positively got to _download_ every motherfucker on the page, accept no substitutes. :grin:"

## Install

1. Clone the repository to your computer

```
  git clone git@bitbucket.org:djb000m/file-downloader.git
```

2. Create a new python virtual environment:

```
  python -m venv {environment_location}

```

3. Activate the virtual environment and Use pip to install the script:

```
  cd {script_directory}
  source {environment_location}/bin/activate
  pip install .
```

4. Run the script:

```
  Usage: download-files [OPTIONS]

  A tool to download all files of a specified file extension, or MIME
  Content-Type, from a given url

Options:
  -u, --url TEXT             The URL to download from
  -f, --file-extension TEXT  Specific file extension to download
  -c, --content-type TEXT    The MIME Content-Type to download. Must be a
                             valid MIME Content-Type:
                             (Application, Audio,
                             Font, Example, Image, Message, Model, Multipart,
                             Text, Video)
  --version                  Show the version and exit.
  --help                     Show this message and exit.


```

> #### Notes:
>
> _If required options are specified then the script will walk you through the missing options_
>
> _Files will be downloaded to a new subdirectory created in your current working directory_
