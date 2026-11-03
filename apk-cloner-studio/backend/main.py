from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import shutil
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AdvancedSecurityPlugin:
    def __init__(self, decompiled_dir: str):
        self.decompiled_dir = decompiled_dir

    def apply_patches(self, app_name: str):
        manifest_path = os.path.join(self.decompiled_dir, "AndroidManifest.xml")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace('<application', '<application android:allowBackup="true"')
            with open(manifest_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        for root, _, files in os.walk(self.decompiled_dir):
            for file in files:
                if file.endswith(".smali"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            smali_code = f.read()
                        if "isRooted" in smali_code or "checkSignature" in smali_code:
                            smali_code = re.sub(r'move-result v(\d+)', r'const/4 v\1, 0x0', smali_code)
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(smali_code)
                    except:
                        pass
        return True

def run_apk_cloner_pipeline(file_path: str, package_name: str, app_name: str):
    workspace = f"/app/workspace/decompiled_{package_name}"
    os.system(f"apktool d {file_path} -o {workspace} -f")
    plugin = AdvancedSecurityPlugin(workspace)
    plugin.apply_patches(app_name)
    output_apk = f"/app/workspace/cloned_{package_name}.apk"
    os.system(f"apktool b {workspace} -o {output_apk}")
    print(f"🎉 تم الانتهاء من هندسة وبناء النسخة الجديدة: {output_apk}")

@app.post("/api/clone")
async def clone_apk(package_name: str, app_name: str, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    os.makedirs("/app/workspace", exist_ok=True)
    upload_path = f"/app/workspace/{file.filename}"
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    background_tasks.add_task(run_apk_cloner_pipeline, upload_path, package_name, app_name)
    return {"status": "success", "message": "بدأت الحاوية في فك الحمايات وهندسة النسخة الجديدة في الخلفية..."}

@app.get("/api/download/{package_name}")
async def download_apk(package_name: str):
    file_path = f"/app/workspace/cloned_{package_name}.apk"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/vnd.android.package-archive', filename=f"cloned_{package_name}.apk")
    return {"status": "error", "message": "الملف لا يزال تحت المعالجة البرمجة أو غير موجود."}
