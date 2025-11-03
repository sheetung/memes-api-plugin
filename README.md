# memePlugin-api

这是一个为 LangBot 开发的表情包插件，通过 API 调用远程的表情包生成服务。


## 安装方法

### Docker 部署

克隆本仓库

```bash
git clone https://github.com/sheetung/meme-generator-extra-docker.git
```

进入项目目录

```bash
cd memegeneratorextradocker
```

通过命令 `docker compose up -d` 启动容器

1. LangBot 通过本地或者非**docker**部署：

运行后可通过 api 方式调用，一般无需修改插件的api url配置，如果docker部署与LangBot不在同一台机器上，需要修改插件的api url配置为docker容器的ip地址，默认端口为2233

插件配置url中填写 `http://localhost:2233` 

2. LangBot 通过docker部署：

需要将LangBot的docker网络与本插件的docker网络连接起来，在`docker-compose.yaml`中添加如下配置：（已默认添加）

插件配置url中填写 `http://meme-generator:2233`


#### 环境变量



| 变量名               | 默认值              | 说明                    |
| -------------------- | ------------------- | ----------------------- |
| `MEME_DIRS`          | `'["/data/memes"]'` | 额外表情路径            |
| `MEME_DISABLED_LIST` | `'[]'`              | 禁用表情列表            |
| `GIF_MAX_SIZE`       | `10.0`              | 限制生成的 gif 文件大小 |
| `GIF_MAX_FRAMES`     | `100`               | 限制生成的 gif 文件帧数 |
| `BAIDU_TRANS_APPID`  | `''`                | 百度翻译 appid          |
| `BAIDU_TRANS_APIKEY` | `''`                | 百度翻译 apikey         |
| `LOG_LEVEL`          | `'INFO'`            | 日志等级                |

## 使用方法

在LangBot市场安装`meme-plugin-api`, 并配置好环境变量

聊天中触发表情列表中的关键词生成表情包

- 例如：
  - 反了  --> 由QQ头像作为图片传入
  - 反了 [此处有张图] --> 由消息中的图片作为图片传入

### 表情列表

请参考 [表情列表](https://github.com/MemeCrafters/meme-generator/wiki/%E8%A1%A8%E6%83%85%E5%88%97%E8%A1%A8) 查看所有支持的表情包关键词

## 适配平台

|    平台    | 状态 |  备注  |
| :--------: | :--: | :----: |
| OneBot V11 |  ✅   | Napcat |

## 更新历史

- v1.0.0 修复重大BUG，发布第一个正式版本
- v0.5.8 完善图片传入逻辑并简化插件体积
- v0.2.4 修复传入文本或者图片的数量导致表情包生成出错的问题
- v0.1.3 增加默认图片使用qq头像
- v0.1.2 完善基础开发


## 问题反馈及功能开发

[![QQ群](https://img.shields.io/badge/QQ群-965312424-green)](https://qm.qq.com/cgi-bin/qm/qr?k=en97YqjfYaLpebd9Nn8gbSvxVrGdIXy2&jump_from=webapi&authKey=41BmkEjbGeJ81jJNdv7Bf5EDlmW8EHZeH7/nktkXYdLGpZ3ISOS7Ur4MKWXC7xIx)