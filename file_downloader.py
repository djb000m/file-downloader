#!/usr/bin/env python

# TODO: Improve the menu? BASIC MENU ADDED for missing options.
# TODO: Warn if attempting to blindly download filetypes which are likely to be large/potentially harmful - e.g. applications
# TODO: Add a --list option to just list out the matching links and not download them.
# Maybe include file sizes? Maybe offer an option to go ahead and download them?
# TODO: break out the download code into its own function that can be called from extension and content-type functions

import os
import click
import regex
import requests
from bs4 import BeautifulSoup
from bs4.element import SoupStrainer
from requests.exceptions import HTTPError

# a list of valid MIME Content-Types
HTTP_CONTENT_TYPES = [
    "Application",
    "Audio",
    "Font",
    "Example",
    "Image",
    "Message",
    "Model",
    "Multipart",
    "Text",
    "Video",
]


def soupify_links(url, file_extension=None):
    """
    Returns a String list containing urls that match the specified file_extension
    Only works on link tags
    
    Args:
        url (String): the target URL
    
    Returns:
        [String]: A list of string URLs representing all links to content from <a> and <img> tags
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"
    }

    with requests.session() as session:

        try:
            # run a GET request on the supplied URL
            r = session.get(url, headers=headers, stream=True, timeout=1)
            r.raise_for_status()
        except HTTPError as http_err:
            click.secho(f"\nHTTP error occurred: {http_err}\n", fg="red", bold=False)
            return False
        except TimeoutError as timeout_err:
            click.secho(f"\nRequest timed out: {timeout_err}\n", fg="red", bold=False)
            return False
        except Exception as err:
            click.secho(f"\nOther error occurred: {err}\n", fg="red", bold=False)
            return False
        else:
            # no errors... continue
            # parse just the <img> and <a> tags
            soup_a = BeautifulSoup(r.content, "lxml", parse_only=SoupStrainer("a"))
            soup_img = BeautifulSoup(r.content, "lxml", parse_only=SoupStrainer("img"))

    # build the list of hrefs
    hrefs = []

    if file_extension is not None:
        print(f"Getting links for {file_extension} files...")
        # Looking for a specific file_extension
        for img_link in soup_img(src=regex.compile(f".{file_extension}")):
            if img_link.get("src") is not None:
                hrefs.append(conv_rel_abs_addr(url, img_link.get("src")))
        for a_link in soup_a(href=regex.compile(f".{file_extension}")):
            if a_link.get("href") is not None:
                hrefs.append(conv_rel_abs_addr(url, a_link.get("href")))
    else:
        print("Getting links...")
        for img_link in soup_img.find_all("img"):
            if img_link.get("src") is not None:
                hrefs.append(conv_rel_abs_addr(url, img_link.get("src")))
        for a_link in soup_a.find_all("a"):
            if a_link.get("href") is not None:
                hrefs.append(conv_rel_abs_addr(url, a_link.get("href")))

    return hrefs


def conv_rel_abs_addr(url, address):
    """
    Takes a string representing a relative address (e.g. /link_to_somewhere) and returns a string representing an absolute adress
    
    Returns:
        String: a string representing an absolute address
    """
    # check to see if the supplied address begins with a '/' - this indicates it is a relative address
    # If not, add it to the address to create an absolute address
    if address[0] == "/":
        address = url.rstrip("/") + "/" + address.lstrip("/")

    # return the address (whether it has been modified or not)
    return address


def download_file_extensions(hrefs, file_extension, save_location):
    """
    Takes a target list of addresses, a required file-extension and attempts downloads for each to the supplied save location
    
    Returns:
        Boolean: Indicates if there is a significant failure, or if the attempts were successful
                 Does not indicate that all files have been downloaded - maybe future return can be (success,failure) list
    """
    # check if a list of hrefs has been supplied
    if hrefs is False:
        # Supplied URL did not return any links
        click.secho(
            f"No links with {file_extension} found on the supplied URL.\n",
            bg="red",
            fg="white",
        )
        return False

    click.echo(
        f"\nI'm going to download some {click.style(file_extension, bold=True, fg='white', bg='blue')} files!\n"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"
    }

    # number of download failures recorded
    errors_list = []

    # create the directory to save the files in
    try:
        os.makedirs(save_location)
    except OSError:
        # the directory already exists, do not try and create it
        pass

    # create an http session and attempt downloads of the identified files
    with requests.session() as session:
        with click.progressbar(
            hrefs, len(hrefs), label="processing links"
        ) as total_reqs:
            for target_addr in total_reqs:
                # if the end of the target address matches the file extension, attempt the download
                if (
                    target_addr[
                        len(target_addr) - len(file_extension) - 1 : len(target_addr)
                    ]
                    == f".{file_extension}"
                ):
                    try:
                        # run a GET request on the supplied address
                        r = session.get(
                            target_addr, headers=headers, stream=True, timeout=1
                        )
                        r.raise_for_status()
                    except HTTPError as http_err:
                        errors_list.append(f"Address: {target_addr}")
                        errors_list.append(f"HTTP error occurred: {http_err}")
                        continue
                    except TimeoutError as timeout_err:
                        errors_list.append(f"Address: {target_addr}")
                        errors_list.append(f"Request timed out: {timeout_err}")
                        continue
                    except Exception as err:
                        errors_list.append(f"Address: {target_addr}")
                        errors_list.append(f"Other error occurred: {err}")
                        continue
                    else:
                        # no errors... write the file out
                        try:
                            # create a new file save it to the specified location
                            with open(
                                save_location + os.sep + r.url.rsplit("/", 1)[1], "wb"
                            ) as handle:
                                for block in r.iter_content(1024):
                                    if not block:
                                        break

                                    handle.write(block)
                        except OSError as os_err:
                            click.secho(
                                f"\nError writing to file: {os_err}\n",
                                fg="red",
                                bold=False,
                            )

    if errors_list:
        click.echo(f"There were {int(len(errors_list)/2)} errors:")
        for err in errors_list:
            click.secho(err, fg="red")

    # everything seems to have worked
    return True


def download_content_types(hrefs, content_type, save_location):
    """
    Takes a target list of addresses, a required MIME Content-Type, checks the link's content-type and attempts a download if matched
    to the supplied save location
    
    Returns:
        Boolean: Indicates if there is a significant failure, or if the attempts were successful
                 Does not indicate that all files have been downloaded - maybe future return can be (success,failure) list
    """
    # check if a list of hrefs has been supplied
    if hrefs is False:
        # Supplied URL did not return any links
        click.secho(f"No links found on the supplied URL.\n", bg="red", fg="white")
        return False

    click.echo(
        f"\nI'm going to download some {click.style(str.title(content_type), bold=True, fg='white', bg='blue')} files!\n"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"
    }

    # number of download failures recorded
    errors_list = []

    # create the directory to save the files in
    try:
        os.makedirs(save_location)
    except OSError:
        # the directory already exists, do not try and create it
        pass

    # create an http session and attempt downloads of the identified files
    with requests.session() as session:
        with click.progressbar(
            hrefs, len(hrefs), label="processing links"
        ) as total_reqs:
            for target_addr in total_reqs:
                try:
                    # run a GET request on the supplied address
                    r = session.get(
                        target_addr, headers=headers, stream=True, timeout=1
                    )
                    r.raise_for_status()
                except HTTPError as http_err:
                    errors_list.append(f"Address: {target_addr}")
                    errors_list.append(f"HTTP error occurred: {http_err}")
                    continue
                except TimeoutError as timeout_err:
                    errors_list.append(f"Address: {target_addr}")
                    errors_list.append(f"Request timed out: {timeout_err}")
                    continue
                except Exception as err:
                    errors_list.append(f"Address: {target_addr}")
                    errors_list.append(f"Other error occurred: {err}")
                    continue
                else:
                    # no errors... check if the returned file is of the correct content-type
                    if r.headers["content-type"][0 : len(content_type)] == content_type:
                        # it is, write the file out
                        try:
                            # create a new file save it to the specified location
                            with open(
                                save_location + os.sep + r.url.rsplit("/", 1)[1], "wb"
                            ) as handle:
                                for block in r.iter_content(1024):
                                    if not block:
                                        break

                                    handle.write(block)
                        except OSError as os_err:
                            click.secho(
                                f"\nError writing to file: {os_err}\n",
                                fg="red",
                                bold=False,
                            )

    if errors_list:
        click.echo(f"There were {int(len(errors_list)/2)} errors:")
        for err in errors_list:
            click.secho(err, fg="red")

    # request the supplied hrefs and identify those that link to the correct MIME Content-Type

    # attempt downloads of the identified files

    # everything seems to have worked
    return True


@click.command()
@click.option("--url", "-u", prompt="\nURL to target", help="The URL to download from")
@click.option("--file-extension", "-f", help="Specific file extension to download")
@click.option(
    "--content-type",
    "-c",
    help="The MIME Content-Type to download. Must be a valid MIME Content-Type: \n\
            (Application, Audio, Font, Example, Image, Message, Model, Multipart, Text, Video)",
)
@click.version_option()
def cli(url, file_extension, content_type):
    """
    A tool to download all files of a specified file extension, or MIME Content-Type, from a given url
    """

    # clear the terminal - it just looks nicer.
    click.clear()

    # handle the user prepending the file extension with stuff
    if file_extension is not None and file_extension[0] == ".":
        file_extension = file_extension[1 : len(file_extension)]

    # handle the user not including an http schema in the URL
    if url[0:7] == "http://" or url[0:8] == "https://":
        # url appears to have a correct schema, do nothing to it
        pass
    else:
        # url does not appear to have a correct schema, add an 'http://' to be compliant with requests module
        # assuming here that the user does not enter ftp, ssh, telnet (etc.) urls
        url = "http://" + url.lstrip("/")

    print(f"having a look at {url}...")

    if file_extension is None and content_type is None:
        # no file extension or Content-Type specified
        click.clear()
        click.secho(
            f"\nYou didn't specify what type of content to download!",
            fg="white",
            bg="red",
        )
        user_input = click.prompt(
            "\nWhat type of content do you want to download? \n \
            \n 1. Files with a specific file extension. \
            \n 2. All files of a a specific content-type. \
            \n 3. None, Quit. \
            \n\n (Choose a menu option)",
            type=int,
        )

        if user_input == 1:
            # prompt the user for a file extension
            click.clear()
            file_extension = click.prompt(
                "Enter the file extension you wish to download (e.g. wav, jpg, png)",
                type=str,
            )

            # download the files
            download_file_extensions(
                soupify_links(url, file_extension),
                file_extension,
                f"{url.rsplit('/',1)[1]+os.sep}downloaded_{file_extension}_files",
            )
        elif user_input == 2:
            # prompt the user for the MIME Content-Type
            click.clear()
            content_type = click.prompt(
                "\nEnter the MIME Content-Type you wish to download",
                type=click.Choice(HTTP_CONTENT_TYPES, case_sensitive=False),
                show_choices=True,
            )

            # download the files
            download_content_types(
                soupify_links(url, file_extension),
                content_type,
                f"{url.rsplit('/',1)[1]+os.sep}downloaded_{content_type}_files",
            )

    elif file_extension is not None and content_type is not None:
        # user wants to download files of a specific type AND all files of a content-type
        # prompt for confirmation
        if click.confirm(
            f"You have selected to download {file_extension} files and all {str.title(content_type)} files. Is this correct?"
        ):

            # get the links from the url
            hrefs = soupify_links(url, file_extension)

            # download file_extensions
            download_file_extensions(
                hrefs,
                file_extension,
                f"{url.rsplit('/',1)[1]+os.sep}downloaded_{file_extension}_files",
            )
            # download content-types
            download_content_types(
                hrefs,
                content_type,
                f"{url.rsplit('/',1)[1]+os.sep}downloaded_{content_type}_files",
            )
    elif file_extension is not None and content_type is None:
        # download file_extensions
        download_file_extensions(
            soupify_links(url, file_extension),
            file_extension,
            f"{url.rsplit('/',1)[1]+os.sep}downloaded_{file_extension}_files",
        )
    else:
        # file_extension is None and content_type is not None:
        # download content-types
        download_content_types(
            soupify_links(url, file_extension),
            content_type,
            f"{url.rsplit('/',1)[1]+os.sep}downloaded_{content_type}_files",
        )
