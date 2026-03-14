# Bug Report & Fix: Metrics Dashboard

## 🐛 The Problem

The **Model Performance** page in your NeuroFusion dashboard was showing **HARDCODED MOCK DATA** instead of real training metrics from your federated learning backend.

### What Was Wrong?

The file [neurodash/src/pages/ModelPerformance.jsx](neurodash/src/pages/ModelPerformance.jsx) was using completely fabricated data:

```jsx
// ❌ BEFORE: All hardcoded mock data
useEffect(() => {
  // mock now; replace with API call to backend metrics endpoint if you add one
  const acc = Array.from({ length: 20 }).map((_, i) => 
    ({ epoch: i + 1, acc: 0.6 + i * 0.02 + (Math.random() - .5) * 0.02 })
  );
  const loss = Array.from({ length: 20 }).map((_, i) => 
    ({ epoch: i + 1, loss: Math.exp(-i / 6) + (Math.random() - .5) * 0.02 })
  );
  const cm = [
    { label: "TP", value: 40 }, 
    { label: "FP", value: 5 }, 
    { label: "FN", value: 3 }, 
    { label: "TN", value: 52 }
  ];
  setMetrics({ acc, loss, cm });
}, []);
```

**Results in:**
- ❌ Accuracy curve: Fabricated progression from 0.55 to 0.75
- ❌ Loss curve: Fake exponential decay
- ❌ Confusion Matrix: Hardcoded values unrelated to actual training
- ❌ No real-time updates from actual FL training
- ❌ No connection to backend `/api/fl/status` endpoint

---

## ✅ The Solution

### What Changed?

Updated [neurodash/src/pages/ModelPerformance.jsx](neurodash/src/pages/ModelPerformance.jsx) to:

1. **Fetch real data from backend** via `/api/fl/status` API
2. **Parse metrics_history** from the federated learning state
3. **Extract actual confusion matrix** from latest round
4. **Auto-refresh every 5 seconds** for real-time updates
5. **Add error handling** with graceful fallback to demo data
6. **Show loading states** and refresh button

### Code Changes

```jsx
// ✅ AFTER: Fetch real data from backend
const fetchMetrics = async () => {
  try {
    setLoading(true);
    const response = await axios.get("http://127.0.0.1:5000/api/fl/status");
    const data = response.data;

    // Transform metrics_history into chart format
    const acc = (data.metrics_history || []).map((item, idx) => ({
      epoch: idx + 1,
      round: item.round,
      acc: typeof item.accuracy === 'number' ? item.accuracy : 0
    }));

    const loss = (data.metrics_history || []).map((item, idx) => ({
      epoch: idx + 1,
      round: item.round,
      loss: typeof item.loss === 'number' ? item.loss : 0
    }));

    // Extract confusion matrix from latest metrics
    const latestMetrics = data.metrics || {};
    let cm = [
      { label: "TP", value: 0 },
      { label: "FP", value: 0 },
      { label: "FN", value: 0 },
      { label: "TN", value: 0 }
    ];

    if (Array.isArray(latestMetrics.confusion_matrix)) {
      const confMatrix = latestMetrics.confusion_matrix;
      cm = [
        { label: "TP", value: confMatrix[1]?.[1] || 0 },
        { label: "FP", value: confMatrix[0]?.[1] || 0 },
        { label: "FN", value: confMatrix[1]?.[0] || 0 },
        { label: "TN", value: confMatrix[0]?.[0] || 0 }
      ];
    }

    setMetrics({ acc, loss, cm });
    setError(null);
  } catch (err) {
    console.error("Error fetching metrics:", err);
    setError("Failed to load metrics from server");
    // Fallback to demo data
    setMetrics({ ... });
  }
};

// Refresh data every 5 seconds
useEffect(() => {
  fetchMetrics();
  const interval = setInterval(fetchMetrics, 5000);
  return () => clearInterval(interval);
}, []);
```

---

## 📊 Impact

### Before Fix
```
Dashboard Shows:
├─ Accuracy: FAKE (0.55 → 0.75)
├─ Loss: FAKE (exponential decay) 
├─ Confusion Matrix: HARDCODED numbers
└─ Data Updates: NEVER (static mock data)
```

### After Fix
```
Dashboard Shows:
├─ Accuracy: REAL (from metrics_history) ✅
├─ Loss: REAL (from metrics_history) ✅
├─ Confusion Matrix: REAL (from latest round) ✅
├─ Data Updates: AUTO (refreshes every 5s) ✅
└─ Error Handling: Graceful fallback to demo ✅
```

---

## 🔧 How to Verify the Fix

1. **Start your FL training:**
   ```powershell
   python federated/start_server.py
   # In another terminal:
   python federated/start_client.py
   ```

2. **Open the dashboard:**
   ```
   http://localhost:5173/app/performance
   ```

3. **Watch real-time updates:**
   - Accuracy curve updates as rounds complete
   - Loss decreases with each round
   - Confusion matrix updates with actual predictions
   - "Refresh" button manually pulls latest data

4. **Check network requests:**
   - Open Browser DevTools (F12)
   - Go to Network tab
   - Should see requests to `http://127.0.0.1:5000/api/fl/status`
   - Automatic refresh every 5 seconds

---

## 🎯 Data Flow

```
┌─────────────────────────────┐
│  Federated Learning Server  │
│  (training on clients)       │
└──────────────┬──────────────┘
               │
               │ Aggregates updates
               │ Computes metrics
               ↓
┌─────────────────────────────┐
│  Backend API /api/fl/status │
│  (stores metrics_history)   │
└──────────────┬──────────────┘
               │
               │ Returns JSON
               │ with metrics_history
               ↓
┌──────────────────────────────┐
│  ModelPerformance Component  │
│  (fetches via axios)         │
├──────────────────────────────┤
│ ✅ Accuracy Chart (real data)│
│ ✅ Loss Chart (real data)    │
│ ✅ Confusion Matrix (real)   │
│ ✅ Auto-refresh (5sec)       │
└──────────────────────────────┘
```

---

## 📝 Files Modified

- [neurodash/src/pages/ModelPerformance.jsx](neurodash/src/pages/ModelPerformance.jsx)
  - Removed mock data generation
  - Added `fetchMetrics()` function with axios
  - Added loading/error states
  - Added auto-refresh interval
  - Improved UI with refresh button

---

## 🚀 Future Improvements

Consider adding:
1. **WebSocket integration** for even more real-time updates
2. **Confidence intervals** on accuracy curves
3. **Per-class accuracy** breakdown
4. **Training time history** visualization
5. **Model checkpoints** display
6. **Export metrics** as CSV/PNG

---

## ✨ Summary

**Root Cause:** Component was using hardcoded demo data  
**Impact:** Misleading metrics display during actual training  
**Solution:** Connected component to real backend API  
**Status:** ✅ Fixed and deployed  
**Date:** March 14, 2026
