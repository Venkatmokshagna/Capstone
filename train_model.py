import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models

# Paths
DATASET_PATH = "dataset"
IMG_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 10

# Create dataset directories if they don't exist
os.makedirs(os.path.join(DATASET_PATH, "clean"), exist_ok=True)
os.makedirs(os.path.join(DATASET_PATH, "contaminated"), exist_ok=True)

# Check if dataset has images before training
clean_count = len(os.listdir(os.path.join(DATASET_PATH, "clean")))
contam_count = len(os.listdir(os.path.join(DATASET_PATH, "contaminated")))

if clean_count == 0 and contam_count == 0:
    print(f"⚠️ Dataset is empty! Please add images to {DATASET_PATH}/clean and {DATASET_PATH}/contaminated before training.")
    exit(1)

# Data generators
train_datagen = ImageDataGenerator(
    rescale=1./255,
    validation_split=0.2,
    rotation_range=20,
    zoom_range=0.2,
    horizontal_flip=True
)

train_generator = train_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='training'
)

val_generator = train_datagen.flow_from_directory(
    DATASET_PATH,
    target_size=(IMG_SIZE, IMG_SIZE),
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='validation'
)

# Base model (Transfer Learning)
base_model = MobileNetV2(
    input_shape=(IMG_SIZE, IMG_SIZE, 3),
    include_top=False,
    weights='imagenet'
)

base_model.trainable = False

# Custom head
x = base_model.output
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dense(128, activation='relu')(x)
x = layers.Dropout(0.5)(x)
output = layers.Dense(1, activation='sigmoid')(x)

model = models.Model(inputs=base_model.input, outputs=output)

# Compile
model.compile(
    optimizer='adam',
    loss='binary_crossentropy',
    metrics=['accuracy']
)

# Train
print("🚀 Starting training...")
history = model.fit(
    train_generator,
    validation_data=val_generator,
    epochs=EPOCHS
)

# Save model
model.save("water_model.h5")

print("✅ Model saved as water_model.h5")
