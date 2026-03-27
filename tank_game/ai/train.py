import os
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from env import TankEnv

def train():
    env = TankEnv()

    # Save a checkpoint every 10000 steps
    checkpoint_callback = CheckpointCallback(
        save_freq=10000,
        save_path='./logs/',
        name_prefix='tank_model'
    )

    # Create the model
    model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="./ppo_tank_tensorboard/")

    # Train the agent
    print("Starting training...")
    model.learn(total_timesteps=50000, callback=checkpoint_callback)

    # Save the final model
    os.makedirs('models', exist_ok=True)
    model.save("models/ppo_tank_final")
    print("Training complete and model saved.")

if __name__ == "__main__":
    train()
