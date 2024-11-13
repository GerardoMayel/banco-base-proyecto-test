# src/utils/model_engineering.py
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Union
from sklearn.preprocessing import MinMaxScaler
import keras
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint
import matplotlib.pyplot as plt

class ModelEngineer:
    """
    Clase para la creación y entrenamiento del modelo predictivo LSTM
    para el tipo de cambio USD/MXN.
    """
    
    def __init__(self):
        self.scalers = {}
        self.sequence_length = 10  # Ventana de tiempo para predicción
        self.model = None
        print(f"Usando Keras versión: {keras.__version__}")
        
    def prepare_data(self, 
                    technical_data: pd.DataFrame,
                    statistical_data: pd.DataFrame,
                    sentiment_data: pd.DataFrame = None,
                    target_col: str = 'usdmxn_fix',
                    test_size: float = 0.2) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
        """
        Prepara los datos para el entrenamiento del modelo LSTM.
        """
        # Combinar todas las características
        features = pd.concat([
            technical_data.select_dtypes(include=[np.number]),
            statistical_data.select_dtypes(include=[np.number])
        ], axis=1)
        
        if sentiment_data is not None:
            sentiment_numeric = sentiment_data.select_dtypes(include=[np.number])
            features = pd.concat([features, sentiment_numeric], axis=1)
        
        # Eliminar columnas duplicadas y NaN
        features = features.loc[:,~features.columns.duplicated()]
        features = features.dropna()
        
        # Separar features y target
        y = features[target_col]
        X = features.drop(target_col, axis=1)
        
        # Escalar datos
        self.scalers['features'] = MinMaxScaler()
        self.scalers['target'] = MinMaxScaler()
        
        X_scaled = self.scalers['features'].fit_transform(X)
        y_scaled = self.scalers['target'].fit_transform(y.values.reshape(-1, 1))
        
        # Crear secuencias
        X_seq, y_seq = self._create_sequences(X_scaled, y_scaled)
        
        # Dividir en train y test
        train_size = int(len(X_seq) * (1 - test_size))
        
        train_data = {
            'X': X_seq[:train_size],
            'y': y_seq[:train_size],
            'features': X.columns.tolist()
        }
        
        test_data = {
            'X': X_seq[train_size:],
            'y': y_seq[train_size:],
            'features': X.columns.tolist()
        }
        
        return train_data, test_data
    
    def _create_sequences(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Crea secuencias para el entrenamiento LSTM.
        """
        X_seq, y_seq = [], []
        
        for i in range(len(X) - self.sequence_length):
            X_seq.append(X[i:(i + self.sequence_length)])
            y_seq.append(y[i + self.sequence_length])
            
        return np.array(X_seq), np.array(y_seq)
    
    def build_model(self, input_shape: Tuple[int, int]) -> None:
        """
        Construye el modelo LSTM.
        """
        self.model = Sequential([
            LSTM(100, return_sequences=True, input_shape=input_shape),
            Dropout(0.3),  # Aumentar la tasa de dropout para evitar overfitting
            LSTM(100, return_sequences=False),  # Aumentar la capacidad del LSTM
            Dropout(0.3),
            Dense(50, activation='relu'),  # Incrementar el número de neuronas en la capa densa
            Dense(1)
        ])
        
        self.model.compile(
            optimizer=Adam(learning_rate=0.0005),  # Reducir la tasa de aprendizaje para un ajuste más cuidadoso
            loss='mse',
            metrics=['mae']
        )
        
    def train_model(self, 
                    train_data: Dict[str, np.ndarray],
                    test_data: Dict[str, np.ndarray],
                    epochs: int = 100,
                    batch_size: int = 32) -> pd.DataFrame:
        """
        Entrena el modelo LSTM.
        """
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=20,  # Aumentar la paciencia para un ajuste más preciso
                restore_best_weights=True
            ),
            ModelCheckpoint(
                'best_model.h5',
                monitor='val_loss',
                save_best_only=True
            )
        ]
        
        history = self.model.fit(
            train_data['X'],
            train_data['y'],
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(test_data['X'], test_data['y']),
            callbacks=callbacks,
            verbose=0
        )
        
        return pd.DataFrame(history.history)
    
    def evaluate_model(self, 
                      test_data: Dict[str, np.ndarray],
                      return_predictions: bool = True) -> Tuple[Dict[str, float], np.ndarray]:
        """
        Evalúa el modelo en el conjunto de prueba.
        """
        metrics = self.model.evaluate(test_data['X'], test_data['y'], verbose=0)
        eval_metrics = dict(zip(self.model.metrics_names, metrics))
        
        if return_predictions:
            predictions = self.model.predict(test_data['X'])
            predictions_unscaled = self.scalers['target'].inverse_transform(predictions)
            return eval_metrics, predictions_unscaled
        
        return eval_metrics, None
    
    def plot_training_history(self, history: pd.DataFrame) -> None:
        """
        Visualiza el historial de entrenamiento.
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Plot loss
        ax1.plot(history['loss'], label='Training Loss')
        ax1.plot(history['val_loss'], label='Validation Loss')
        ax1.set_title('Model Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        
        # Plot MAE
        ax2.plot(history['mae'], label='Training MAE')
        ax2.plot(history['val_mae'], label='Validation MAE')
        ax2.set_title('Model MAE')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('MAE')
        ax2.legend()
        
        plt.tight_layout()
        plt.show()