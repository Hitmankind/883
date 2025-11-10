# Django学生成绩管理系统 - Linux部署指南

本文档提供了在Linux环境下使用Nginx和Gunicorn部署Django学生成绩管理系统的详细步骤。

## 前提条件

- Linux系统（Ubuntu/Debian/CentOS等）
- Python 3.8+
- pip
- Nginx

## 步骤一：安装必要的软件包

### Ubuntu/Debian

```bash
# 更新软件包列表
apt update

# 安装Python、pip、Nginx和其他必要依赖
apt install -y python3 python3-pip python3-venv nginx
```

### CentOS/RHEL

```bash
# 安装EPEL仓库
yum install epel-release

# 安装Python、pip、Nginx和其他必要依赖
yum install -y python3 python3-pip nginx
```

## 步骤二：设置项目环境

### 1. 克隆项目（如果尚未克隆）

```bash
# 假设您已经将项目放在/root/Django学生成绩管理目录
cd /root/Django学生成绩管理
```

### 2. 创建并激活虚拟环境（推荐）

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 3. 安装项目依赖

```bash
# 安装依赖包
pip install -r requirements.txt
```

## 步骤三：配置Django项目

### 1. 修改settings.py中的配置

请根据您的服务器情况修改以下配置：

```python
# 允许的主机列表
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'your-server-ip']

# 您还可以修改SECRET_KEY为更安全的值
```

### 2. 运行数据库迁移（如果需要）

```bash
# 确保在虚拟环境中执行
python manage.py migrate
```

### 3. 收集静态文件

```bash
python manage.py collectstatic --noinput
```

## 步骤四：配置Nginx

### 1. 将nginx.conf复制到Nginx配置目录

```bash
# Ubuntu/Debian
cp nginx.conf /etc/nginx/sites-available/django_grade_management

# 创建符号链接
ln -s /etc/nginx/sites-available/django_grade_management /etc/nginx/sites-enabled/

# CentOS/RHEL
cp nginx.conf /etc/nginx/conf.d/django_grade_management.conf
```

### 2. 测试Nginx配置

```bash
nginx -t
```

### 3. 重启Nginx服务

```bash
# Ubuntu/Debian
systemctl restart nginx

# CentOS/RHEL
service nginx restart
```

## 步骤五：启动Gunicorn服务

### 1. 使用提供的启动脚本

```bash
# 如果使用了虚拟环境，请确保已激活
# source venv/bin/activate

# 启动Gunicorn
./start_gunicorn.sh
```

### 2. 配置Gunicorn为系统服务（推荐，可选）

创建Gunicorn系统服务文件：

```bash
nano /etc/systemd/system/gunicorn_grade_management.service
```

添加以下内容：

```
[Unit]
Description=Gunicorn daemon for Django grade management system
After=network.target

[Service]
User=root
WorkingDirectory=/root/Django学生成绩管理
ExecStart=/root/Django学生成绩管理/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 grade_management.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

启动并设置开机自启：

```bash
systemctl daemon-reload
systemctl start gunicorn_grade_management
systemctl enable gunicorn_grade_management
```

## 步骤六：配置防火墙（如果需要）

### Ubuntu/Debian

```bash
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### CentOS/RHEL

```bash
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload
```

## 访问系统

完成上述配置后，您可以通过以下方式访问系统：

- 浏览器访问：`http://your-server-ip` 或 `http://localhost`

## 故障排除

### 常见问题

1. **Nginx启动失败**
   - 检查配置文件语法：`nginx -t`
   - 查看错误日志：`journalctl -u nginx`

2. **Gunicorn无法启动**
   - 检查Python环境和依赖是否正确安装
   - 查看Gunicorn日志：`cat gunicorn.log`

3. **静态文件无法访问**
   - 确保已运行`collectstatic`命令
   - 检查Nginx配置中的静态文件路径是否正确
   - 检查文件权限是否正确

4. **502 Bad Gateway错误**
   - 检查Gunicorn服务是否正在运行
   - 检查Nginx配置中的upstream设置是否正确

### 日志文件

- Nginx错误日志：`/var/log/nginx/error.log`
- Nginx访问日志：`/var/log/nginx/access.log`
- Gunicorn日志：项目目录下的`gunicorn.log`

## 注意事项

1. 生产环境中请确保使用强密码和安全配置
2. 定期备份数据库和重要文件
3. 考虑配置HTTPS以增强安全性
4. 根据服务器性能调整Gunicorn的worker数量

## 更新项目

当需要更新项目代码时：

1. 拉取最新代码
2. 激活虚拟环境
3. 更新依赖（如果有变化）
4. 运行数据库迁移（如果有变化）
5. 收集静态文件
6. 重启Gunicorn服务

```bash
# 拉取代码后执行
cd /root/Django学生成绩管理
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart gunicorn_grade_management
```