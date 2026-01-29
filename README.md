# memePlugin-api

This is a meme plugin developed for LangBot, which generates memes by calling a remote meme generation service via API.


## Installation

### Docker Deployment

Clone this repository

```bash
git clone https://github.com/sheetung/meme-generator-extra-docker.git
```

Enter the project directory

```bash
cd memegeneratorextradocker
```

Start the container using `docker compose up -d`

1. LangBot deployed locally or **not via Docker**:

After running, it can be accessed via API. Generally, no modification to the plugin API URL configuration is required.  
If the Docker deployment and LangBot are not on the same machine, you need to modify the plugin API URL to the Docker container's IP address.  
The default port is `2233`.

Set the plugin configuration URL to:

```
http://localhost:2233
```

2. LangBot deployed via Docker:

You need to connect the Docker network of LangBot with the Docker network of this plugin.  
Add the following configuration to `docker-compose.yaml` (already added by default):

Set the plugin configuration URL to:

```
http://meme-generator:2233
```


#### Environment Variables

| Variable Name        | Default Value       | Description                     |
| -------------------- | ------------------- | ------------------------------- |
| `MEME_DIRS`          | `'["/data/memes"]'` | Additional meme directories     |
| `MEME_DISABLED_LIST` | `'[]'`              | Disabled meme list              |
| `GIF_MAX_SIZE`       | `10.0`              | Maximum generated GIF file size |
| `GIF_MAX_FRAMES`     | `100`               | Maximum number of GIF frames    |
| `BAIDU_TRANS_APPID`  | `''`                | Baidu Translate appid           |
| `BAIDU_TRANS_APIKEY` | `''`                | Baidu Translate apikey          |
| `LOG_LEVEL`          | `'INFO'`            | Log level                       |

## Usage

Install `meme-plugin-api` from the LangBot marketplace and configure the environment variables.

Trigger meme generation in chat using keywords from the meme list.

- Examples:
  - 反了  --> Uses QQ avatar as the input image
  - 反了 [an image here] --> Uses the image in the message as the input


### Meme List

Please refer to the following links to get meme information:

- [Meme List 1](https://github.com/MemeCrafters/meme-generator/wiki/%E8%A1%A8%E6%83%85%E5%88%97%E8%A1%A8) 
- [Meme List 2](https://github.com/anyliew/meme_emoji/wiki/%E8%A1%A8%E6%83%85%E5%88%97%E8%A1%A8)


## Supported Platforms

|  Platform  | Status | Remarks |
| :--------: | :----: | :-----: |
| OneBot V11 |   ✅    | Napcat  |

## Changelog

- v1.2.0: Added additional memes (Please update the usage in the Docker repository accordingly)
- v1.1.0 Improved meme information handling mechanism  
- v1.0.0 Fixed critical bugs and released the first stable version  
- v0.5.8 Improved image input logic and reduced plugin size  
- v0.2.4 Fixed issues caused by incorrect numbers of text or image inputs  
- v0.1.3 Added default image using QQ avatar  
- v0.1.2 Improved basic development


## Meme-related Repositories

- [meme-generator](https://github.com/MemeCrafters/meme-generator)
- [meme_emoji](https://github.com/anyliew/meme_emoji)


## Feedback & Feature Requests

[![QQ Group](https://img.shields.io/badge/QQ%20Group-965312424-green)](https://qm.qq.com/cgi-bin/qm/qr?k=en97YqjfYaLpebd9Nn8gbSvxVrGdIXy2&jump_from=webapi&authKey=41BmkEjbGeJ81jJNdv7Bf5EDlmW8EHZeH7/nktkXYdLGpZ3ISOS7Ur4MKWXC7xIx)