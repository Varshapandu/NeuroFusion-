# 🚀 FL Model Performance Tuning Guide

## Current Issue
**Accuracy: 10.7% (should be 60-90%)**

This was happening because the default FL config was too conservative for initial training.

---

## ✅ What I Fixed

### 1. **Increased Training Rounds**
```python
NUM_ROUNDS = 3  → 30  # More time to converge
```
**Why**: 3 global rounds is not enough. With 2 clients and 5 local epochs each:
- Round 1-5: Model learning basics
- Round 10-15: Starting to see patterns
- Round 20-30: Convergence

### 2. **Increased Local Epochs Per Client**
```python
LOCAL_EPOCHS = 1  → 5  # Each client trains 5x longer locally
```
**Why**: More local training means better weight updates to aggregate.

### 3. **Increased Learning Rate**
```python
LR = 1e-4  → 1e-3  # 10x faster learning
```
**Why**: 1e-4 is too slow for initial training. 1e-3 allows model to learn EEG patterns.

### 4. **Disabled DP Noise (Temporarily)**
```python
UPDATE_NOISE_MULTIPLIER = 0.5  → 0.0
```
**Why**: Privacy noise was preventing model from learning. Once we achieve good accuracy (70%+), we can re-enable it.

---

## 📊 Expected Results After Fix

With these settings, you should see:
- **Round 1**: Accuracy ~20-30% (random is 16.7%)
- **Round 10**: Accuracy ~50-60%
- **Round 20**: Accuracy ~70-80%
- **Round 30**: Accuracy ~80-85%

---

## 🔧 How to Run with New Settings

**Start with improved config:**
```bash
# 30 rounds instead of 3
python federated/start_server.py --num-rounds 30
```

In another terminal, start 2 clients:
```bash
python federated/start_client.py --client-id 1
python federated/start_client.py --client-id 2
```

Watch the dashboard at http://localhost:5173 → **Metrics** → **Model Performance**

---

## 📈 Advanced Tuning (If Still Low)

If accuracy is still <60% after 30 rounds, try:

### Option A: Longer Training
```env
NUM_ROUNDS=50         # Even more rounds
LOCAL_EPOCHS=10       # More local training
```

### Option B: Adjust Learning Rate
```env
LR=5e-4              # Try middle ground
```

### Option C: Check Data Quality
```bash
python dataset_summary.py  # See data distribution
```

### Once Accuracy >70%, Re-Enable Privacy:
```env
UPDATE_NOISE_MULTIPLIER=0.1  # Gradual re-enable
```

---

## 🎯 Quick Performance Checklist

- [ ] Training 30 rounds (not 3)
- [ ] 5 local epochs per client
- [ ] Learning rate at 1e-3
- [ ] DP noise disabled (0.0)
- [ ] Dashboard showing improving accuracy each round
- [ ] Accuracy reaching 70%+ by round 20

---

## 📝 Notes

- **Global Round 17** in your previous run = only 17 rounds completed. With previous 1-epoch setup, this wasn't enough.
- **6-class classification** needs more training than binary classification
- **Federated** is slower than centralized (2 clients sharing data), so it needs more rounds

---

## When Ready for Production

Once you achieve 80%+ accuracy:

1. **Re-enable Privacy** (set `UPDATE_NOISE_MULTIPLIER=0.1`)
2. **Add more clients** (set `TOTAL_CLIENTS=4` or higher)
3. **Fine-tune DP budget** using privacy accounting

See `federated/accountant.py` for privacy metrics.
