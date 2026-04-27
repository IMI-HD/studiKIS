# Database Snapshot Comparison

## Step 1 to 2: 2_patient_created
### Database: `odoo`
| Table | Old Count | New Count | Difference |
|-------|-----------|-----------|------------|
| `failed_event_retry_log` | 852 | 937 | +85 |

## Step 2 to 3: 3_lab_order_placed
### Database: `clinlims`
| Table | Old Count | New Count | Difference |
|-------|-----------|-----------|------------|
| `analysis` | 0 | 1 | +1 |
| `external_reference` | 877 | 878 | +1 |
| `history` | 480993 | 481000 | +7 |
| `markers` | 1 | 3 | +2 |
| `patient` | 0 | 1 | +1 |
| `patient_identity` | 0 | 1 | +1 |
| `person` | 0 | 1 | +1 |
| `sample` | 0 | 1 | +1 |
| `sample_human` | 0 | 1 | +1 |
| `sample_item` | 0 | 1 | +1 |

### Database: `odoo`
| Table | Old Count | New Count | Difference |
|-------|-----------|-----------|------------|
| `failed_event_retry_log` | 937 | 954 | +17 |
| `failed_events` | 643 | 644 | +1 |
| `markers` | 3 | 5 | +2 |

## Step 3 to 4: 4_sample_collected
### Database: `clinlims`
| Table | Old Count | New Count | Difference |
|-------|-----------|-----------|------------|
| `event_records` | 0 | 1 | +1 |
| `history` | 481000 | 481003 | +3 |
| `patient` | 1 | 2 | +1 |
| `person` | 1 | 2 | +1 |
| `provider` | 0 | 1 | +1 |

### Database: `odoo`
| Table | Old Count | New Count | Difference |
|-------|-----------|-----------|------------|
| `failed_event_retry_log` | 954 | 968 | +14 |
| `failed_events` | 644 | 645 | +1 |

## Step 4 to 5: 5_result_entered
### Database: `clinlims`
| Table | Old Count | New Count | Difference |
|-------|-----------|-----------|------------|
| `history` | 481003 | 481006 | +3 |
| `result` | 0 | 1 | +1 |
| `result_signature` | 0 | 1 | +1 |
| `test_status` | 0 | 1 | +1 |

### Database: `odoo`
| Table | Old Count | New Count | Difference |
|-------|-----------|-----------|------------|
| `failed_event_retry_log` | 968 | 979 | +11 |

## Step 5 to 6: 6_validated
### Database: `clinlims`
| Table | Old Count | New Count | Difference |
|-------|-----------|-----------|------------|
| `event_records` | 1 | 2 | +1 |
| `history` | 481006 | 481008 | +2 |

### Database: `odoo`
| Table | Old Count | New Count | Difference |
|-------|-----------|-----------|------------|
| `failed_event_retry_log` | 979 | 985 | +6 |

