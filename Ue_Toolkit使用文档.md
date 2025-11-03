# Ue_Toolkit使用文档

此工具箱支持资产管理，工程配置管理，网站推荐，主题自定义。

感谢您能购买此工具箱，接下来我将详细介绍Ue_Toolkit的使用方法和注意事项，内容不长，希望可以耐心看完。


---

## 1. 资产管理

### 1.1 设置资产库路径

首次进入程序或者之前设置过的资产路径不在了，就会弹出设置资产库路径的弹窗，设置好之后，导入的资产就会保存在设置的资产库路径下并自动分类。  
![image-20251031170237441](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031170237441.png)


### 1.2 添加资产

当设置好资产库路径之后，就会进入资产管理的界面，现在就可以开始添加资产了。添加资产的方式有两种：  
点击添加资产按钮或将资产拖入资产管理的内容区域。  
![image-20251031170936028](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031170936028.png)

完成上述操作后，就会弹出添加资产的窗口，需要选择资产所在路径，设置资产名称（它不会改变资产原来的名称），选择分类，是否创建说明文档（如果勾选了这个选项，点击添加之后，就会弹窗文档编辑的窗口，如有需要可对资产进行详细说明）。

在这里我对资产类型进行一个详细的说明，我了解到的资源大概分为两种：资产包和资源文件。

首先来说资源包，它一般是  
**资源名称/content/资源名称/资产**  
或者  
**资源名称/data/资源名称/资产** 的形式。

它必须要将其 data 或 content 下的整个文件夹复制到工程目录下的 content 文件夹下，工程才可以正常读取。

其次是资源文件，它一般是 fbx、wav、png、obj 等格式的单个资源文件。它导入的话，是不用担心资源的路径引用的，直接导入即可。

因此如果是要添加在网上下载的资产，看看它有没有 content 或 data 等类似的目录，在选择资产路径时必须选择这两个目录下的文件才可以添加，拖拽添加也一样，要确保你拖拽的是 content 或 data 下的文件。

一般如果是拖拽添加，工具会自动识别拖拽进来的是资源包还是资源文件；如果是点击添加资产的按钮添加，在选择资产路径前会弹出一个菜单，选择要添加的是资源包还是资源文件然后再选择对应路径。

我更推荐拖拽添加的方式，不过拖拽的文件要严格遵守上面说明的规则，否则会造成预览资产或者将资产迁移到其他工程丢失引用。  
![image-20251031173737416](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031173737416.png)


### 1.3 资产相关操作

添加完成之后，资产就会出现在内容界面，现在可以看到，资产的缩略图默认显示的是资产类型。接下来会详细说明资产的相关操作。  
![image-20251031174324464](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031174324464.png)


#### 1.3.1 查看/修改文档

若在创建时勾选了创建说明文档，想要查看的话，鼠标左键单击资产卡片即可，就会打开资产的文档。  
我的建议是添加资产的时候创建文档，如果资产有什么特殊的地方，可以编辑文档进行说明。  
![image-20251031174557736](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031174557736.png)


#### 1.3.2 预览资产、缩略图管理

预览资产之前，首先需要设置预览工程的路径，需要自行创建一个虚幻工程，建议命名为 预览工程+工程版本，如：预览工程4_26。

创建好工程之后，就可以设置预览工程了：  
点击设置 → 切换到设置界面 → 找到预览工程设置的地方 → 点击添加工程 → 路径选择创建的预览工程的路径。  

预览工程可以设置多个，如果有不同版本，可以创建多个不同版本的预览工程然后添加。添加完之后会提示设置预览工程的名称，建议以工程版本命名，如：4.26 或 5.4。  
![image-20251031175344482](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031175344482.png)

添加好预览工程之后，回到资产管理页面，点击资产卡片的预览资产按钮。  
![image-20251031175703012](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031175703012.png)

等待几秒后就会打开预览工程。  
![image-20251031175902182](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031175902182.png)

现在可以对资产进行查看了。由于我用的是一个测试文件夹，里面什么都没有是正常的。

---

接下来是缩略图的创建方法。缩略图的创建方法非常简单，只要预览过一次工程，关闭后，缩略图会自动设置退出工程前的画面。  

但我不推荐这样做，因为这样的话每次预览缩略图就会改变。如果想让缩略图固定不变，可以用下面的方法：

在工程中进行高分辨率截图，首先将视角调整到一个自己想要的角度，然后按如图所示进行操作。  
![image-20251031180448844](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031180448844.png)

截图完成后关闭工程，资产缩略图就会自动同步，且下一次预览缩略图也会保持原样不会改变。如果在这种情况下想更换缩略图也很简单，预览资产，然后进行上述高分辨率截图操作即可。  
![image-20251031180717085](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031180717085.png)


#### 1.3.3 迁移到工程

点击资产卡片右下角，会弹出右键菜单，点击迁移到工程。  
![image-20251031180926529](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031180926529.png)

![image-20251031181027555](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031181027555.png)

等待几秒后，会显示在电脑中找到的虚幻工程，缩略图右下角显示的是工程版本。  
![image-20251031181042986](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031181042986.png)

想要将资产应用到哪个工程，选中再点击确定即可。

如果不想将整个资产包迁移到其他工程怎么办？  
很简单，预览这个资产，将需要用到的迁移到目标工程即可。


#### 1.3.4 分类管理

在资产管理的分类下拉框旁边可以看到一个齿轮图标，点击它会打开分类管理窗口，可以进行分类的添加和删除。  
![image-20251031181801950](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031181801950.png)


---

## 2. 配置工具

点击左侧工具栏的配置工具切换到配置工具的界面，点击添加配置按钮，会搜索电脑中所有的工程。  

选择想要添加配置的工程，会打开此工程的配置文件，选择需要保存的配置文件，可选多个。  
![image-20251031182641429](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031182641429.png)

![image-20251031182720293](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031182720293.png)

![image-20251031182756221](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031182756221.png)

可以看到配置成功添加了。  
![image-20251031182959962](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031182959962.png)

如果想将添加的配置应用到工程，鼠标左键点击要使用的配置，会弹出搜索到的工程界面。  

想将配置应用到哪个工程选择对应的工程即可。  

（注意：应用配置到工程时，工程需要关闭，否则会导致配置应用失败）


---

## 3. 站点推荐

点击站点推荐，里面有一些我经常用到的网站，有些需要魔法才可以访问。  
![image-20251031183611027](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031183611027.png)


---

## 4. 主题管理

工具箱支持自定义主题，切换到设置界面，可以看到导入主题文件的按钮。  
接下来我将详细介绍主题的配置格式。  
![image-20251031183952876](C:\Users\wang\AppData\Roaming\Typora\typora-user-images\image-20251031183952876.png)


### 4.1 主题基本结构

主题文件是 json 格式的，包含主题名称和颜色变量的定义。

```json
{
  "name": "主题名称",
  "variables": {
    "颜色变量名": "颜色值",
    "另一个颜色变量": "颜色值"
  }
}
主题示例参考：

json
复制代码
{
  "name": "custom",
  "variables": {
    "bg_primary": "#1a1a2e",
    "bg_secondary": "#16213e",
    "bg_tertiary": "#0f3460",
    "bg_hover": "#533483",
    "bg_pressed": "#1a1a2e",
    "text_primary": "#eaeaea",
    "text_secondary": "#c4c4c4",
    "text_tertiary": "#a0a0a0",
    "text_disabled": "#6b6b6b",
    "accent": "#e94560",
    "accent_hover": "#f27289",
    "accent_pressed": "#c7254e",
    "border": "#0f3460",
    "border_hover": "#e94560",
    "border_focus": "#f27289",
    "success": "#00d9ff",
    "warning": "#ffa500",
    "error": "#e94560",
    "info": "#00d9ff",
    "bg_primary_alpha": "rgba(26, 26, 46, 0.85)",
    "bg_secondary_alpha": "rgba(22, 33, 62, 0.8)",
    "accent_alpha": "rgba(233, 69, 96, 0.8)"
  }
}
4.2 主题变量说明
（此处保持原始表格与说明格式）

5. 注意事项
在资产管理界面中删除资产会直接删除资产。