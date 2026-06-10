# -*- coding: utf-8 -*-
"""
GAN Image Generation on MNIST - Higher Resolution Extension

Extension Task for GANs:
Generate Higher Resolution Images.
Adapt the network architecture to generate higher resolution images than 28x28,
perhaps by progressively increasing the output size or using more sophisticated
upsampling techniques.

In this script:
- Original MNIST images are resized from 28x28 to 64x64.
- Generator is modified to generate 64x64 images.
- Discriminator is modified to classify 64x64 images as real or fake.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader, Subset
import matplotlib.pyplot as plt
from pathlib import Path


# -----------------------------
# Generator Block
# -----------------------------
class Generator(nn.Module):
    def __init__(self, z_dim):
        super().__init__()

        self.model = nn.Sequential(
            # Input: z_dim x 1 x 1

            nn.ConvTranspose2d(z_dim, 512, 4, 1, 0),   # 1x1 -> 4x4
            nn.BatchNorm2d(512),
            nn.ReLU(),

            nn.ConvTranspose2d(512, 256, 4, 2, 1),     # 4x4 -> 8x8
            nn.BatchNorm2d(256),
            nn.ReLU(),

            nn.ConvTranspose2d(256, 128, 4, 2, 1),     # 8x8 -> 16x16
            nn.BatchNorm2d(128),
            nn.ReLU(),

            nn.ConvTranspose2d(128, 64, 4, 2, 1),      # 16x16 -> 32x32
            nn.BatchNorm2d(64),
            nn.ReLU(),

            nn.ConvTranspose2d(64, 1, 4, 2, 1),        # 32x32 -> 64x64
            nn.Tanh()
        )

    def forward(self, x):
        return self.model(x)


# -----------------------------
# Discriminator Block
# -----------------------------
class Discriminator(nn.Module):
    def __init__(self):
        super().__init__()

        self.model = nn.Sequential(
            # Input: 1 x 64 x 64

            nn.Conv2d(1, 64, 4, 2, 1),       # 64x64 -> 32x32
            nn.LeakyReLU(0.2),

            nn.Conv2d(64, 128, 4, 2, 1),     # 32x32 -> 16x16
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2),

            nn.Conv2d(128, 256, 4, 2, 1),    # 16x16 -> 8x8
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2),

            nn.Conv2d(256, 512, 4, 2, 1),    # 8x8 -> 4x4
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2),

            nn.Flatten(),
            nn.Linear(512 * 4 * 4, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        return self.model(x)


# -----------------------------
# Device Setup
# -----------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)


# -----------------------------
# Hyperparameters
# -----------------------------
batch_size = 128
lr = 0.0002
z_dim = 100
epochs = 2
image_size = 64
max_samples = 2048
output_dir = Path(__file__).parent / "gan_outputs"
output_dir.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Dataset Loading
# -----------------------------
transform = transforms.Compose([
    transforms.Resize(image_size),          # Resize MNIST from 28x28 to 64x64
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))    # Convert image range from [0,1] to [-1,1]
])

dataset = datasets.MNIST(
    root="./data",
    train=True,
    download=True,
    transform=transform
)

if max_samples:
    dataset = Subset(dataset, range(max_samples))

dataloader = DataLoader(
    dataset,
    batch_size=batch_size,
    shuffle=True
)


# -----------------------------
# Initialize Models, Loss, Optimizers
# -----------------------------
criterion = nn.BCELoss()

generator = Generator(z_dim).to(device)
discriminator = Discriminator().to(device)

optimizer_g = optim.Adam(
    generator.parameters(),
    lr=lr,
    betas=(0.5, 0.999)
)

optimizer_d = optim.Adam(
    discriminator.parameters(),
    lr=lr,
    betas=(0.5, 0.999)
)


# -----------------------------
# Function to Save Images
# -----------------------------
def save_images(images, title, filename):
    images = images.detach().cpu()[:16]

    fig, axes = plt.subplots(4, 4, figsize=(6, 6))
    fig.suptitle(title)

    for i, ax in enumerate(axes.flatten()):
        ax.imshow(images[i].squeeze(), cmap="gray")
        ax.axis("off")

    save_path = output_dir / filename
    plt.savefig(save_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved image grid: {save_path}")


# -----------------------------
# Training Loop
# -----------------------------
for epoch in range(epochs):

    for real, _ in dataloader:
        real = real.to(device)
        current_batch_size = real.size(0)

        # -----------------------------
        # Train Discriminator
        # -----------------------------

        # Generate fake images
        noise = torch.randn(current_batch_size, z_dim, 1, 1).to(device)
        fake = generator(noise)

        # Real labels with label smoothing
        real_labels = torch.ones(current_batch_size, 1).to(device) * 0.9

        # Fake labels
        fake_labels = torch.zeros(current_batch_size, 1).to(device)

        # Discriminator loss on real images
        D_real = discriminator(real)
        loss_real = criterion(D_real, real_labels)

        # Discriminator loss on fake images
        # detach() is used so Generator is not trained here
        D_fake = discriminator(fake.detach())
        loss_fake = criterion(D_fake, fake_labels)

        # Total discriminator loss
        loss_D = loss_real + loss_fake

        optimizer_d.zero_grad()
        loss_D.backward()
        optimizer_d.step()

        # -----------------------------
        # Train Generator
        # -----------------------------

        # Generator wants discriminator to classify fake images as real
        output = discriminator(fake)
        loss_G = criterion(output, real_labels)

        optimizer_g.zero_grad()
        loss_G.backward()
        optimizer_g.step()

    # -----------------------------
    # Show Images After Each Epoch
    # -----------------------------
    print(
        f"Epoch [{epoch + 1}/{epochs}], "
        f"Loss D: {loss_D.item():.4f}, "
        f"Loss G: {loss_G.item():.4f}"
    )

    save_images(
        real,
        "Real MNIST Images - 64x64",
        f"epoch_{epoch + 1}_real.png"
    )
    save_images(
        fake,
        "Generated Fake Images - 64x64",
        f"epoch_{epoch + 1}_fake.png"
    )


# -----------------------------
# Generate Final Images
# -----------------------------
noise = torch.randn(16, z_dim, 1, 1).to(device)
final_fake_images = generator(noise)

save_images(
    final_fake_images,
    "Final Generated 64x64 Images",
    "final_generated.png"
)
