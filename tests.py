import torch
from torchvision import models, transforms
from PIL import Image
from pathlib import Path


# =========================
# 1. Load model pretrained
# =========================

weights = models.ResNet50_Weights.DEFAULT
model = models.resnet50(weights=weights)

# Hilangkan layer klasifikasi terakhir
model.fc = torch.nn.Identity()

model.eval()


# =========================
# 2. Transform gambar
# =========================

transform = weights.transforms()


# =========================
# 3. Fungsi mengambil fitur
# =========================

def extract_feature(image_path):
    image = Image.open(image_path).convert("RGB")

    image = transform(image)
    image = image.unsqueeze(0)

    with torch.no_grad():
        feature = model(image)

    feature = feature / feature.norm(dim=1, keepdim=True)

    return feature


# =========================
# 4. Dataset OREO
# =========================

dataset_path = Path("dataset/oreo")

oreo_images = list(dataset_path.glob("*.jpg"))

print("Jumlah gambar OREO:", len(oreo_images))


# =========================
# 5. Ambil fitur semua OREO
# =========================

oreo_features = []

for image_path in oreo_images:
    feature = extract_feature(image_path)
    oreo_features.append(feature)


# =========================
# 6. Gambar yang akan dites
# =========================

test_image = oreo_images[0]

print("Gambar test:", test_image)


# =========================
# 7. Ambil fitur gambar test
# =========================

test_feature = extract_feature(test_image)


# =========================
# 8. Hitung kemiripan
# =========================

similarities = []

for feature in oreo_features:
    similarity = torch.cosine_similarity(
        test_feature,
        feature
    )

    similarities.append(similarity.item())


average_similarity = sum(similarities) / len(similarities)


# =========================
# 9. Tampilkan hasil
# =========================

print()
print("=== HASIL DETEKSI ===")
print("Produk      : OREO")
print("Similarity  :", round(average_similarity, 4))