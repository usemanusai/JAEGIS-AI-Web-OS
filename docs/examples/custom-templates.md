# 🎨 Custom Templates Guide

## 📋 **Overview**

Learn how to create and use custom templates with JAEGIS AI Web OS to generate projects for any framework or technology stack not included in the default templates.

---

## 🏗️ **Template Structure**

### **Directory Layout**

```
custom_templates/
├── my-framework/
│   ├── template.yaml          # Template configuration
│   ├── files/                 # Template files
│   │   ├── src/
│   │   │   └── main.py.j2
│   │   ├── requirements.txt.j2
│   │   └── README.md.j2
│   └── hooks/                 # Pre/post generation hooks
│       ├── pre_generate.py
│       └── post_generate.py
```

---

**For complete custom templates guide, see the full documentation in the repository.**