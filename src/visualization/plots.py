
from pathlib import Path
import matplotlib.pyplot as plt

def save_ecg_plot(time_s, raw, filtered, peaks, output_path, title="ECG Analysis"):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(14, 6))

    ax.plot(time_s, raw, alpha=0.35, label="Raw ECG")
    ax.plot(time_s, filtered, linewidth=1.5, label="Filtered ECG")

    if len(peaks):
        ax.scatter(
            time_s.iloc[peaks],
            filtered[peaks],
            s=24,
            label="Detected R peaks"
        )

    ax.set_title(title)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Voltage (mV)")
    ax.grid(True, alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)

def save_frequency_plot(frequencies, magnitude, output_path, title="Frequency Spectrum"):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(frequencies, magnitude)
    ax.set_xlim(0, min(50, frequencies.max()))
    ax.set_title(title)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Magnitude")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
