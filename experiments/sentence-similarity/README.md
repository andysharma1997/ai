````git clone https://github.com/pytorch/fairseq.git```
```cd fairseq/```
```pip3 install regex```
```pip3 install fairseq```


```wget https://gist.githubusercontent.com/W4ngatang/60c2bdb54d156a41194446737ce03e2e/raw/17b8dd0d724281ed7c3b2aeeda662b92809aadd5/download_glue_data.py```
```python download_glue_data.py --data_dir glue_data --tasks STS```



```./examples/roberta/preprocess_GLUE_tasks.sh glue_data STS-B```



```
TOTAL_NUM_UPDATES=3598  # 10 epochs through RTE for bsz 16
WARMUP_UPDATES=214      # 6 percent of the number of updates
LR=2e-05                # Peak LR for polynomial LR scheduler.
NUM_CLASSES=1
MAX_SENTENCES=16        # Batch size.
ROBERTA_PATH=/root/roberta.large/model.pt
```

```
CUDA_VISIBLE_DEVICES=0 python train.py STS-B-bin/ \
    --restore-file $ROBERTA_PATH \
    --max-positions 512 \
    --max-sentences $MAX_SENTENCES \
    --max-tokens 4400 \
    --task sentence_prediction \
    --reset-optimizer --reset-dataloader --reset-meters \
    --required-batch-size-multiple 1 \
    --init-token 0 --separator-token 2 \
    --arch roberta_large \
    --criterion sentence_prediction \
    --num-classes $NUM_CLASSES \
    --dropout 0.1 --attention-dropout 0.1 \
    --weight-decay 0.1 --optimizer adam --adam-betas "(0.9, 0.98)" --adam-eps 1e-06 \
    --clip-norm 0.0 \
    --lr-scheduler polynomial_decay --lr $LR --total-num-update $TOTAL_NUM_UPDATES --warmup-updates $WARMUP_UPDATES \
    --fp16 --fp16-init-scale 4 --threshold-loss-scale 1 --fp16-scale-window 128 \
    --max-epoch 10 \
    --find-unused-parameters \
    --best-checkpoint-metric accuracy --regression-target --best-checkpoint-metric loss;
```

```
roberta = RobertaModel.from_pretrained(
    '/root/fairseq/checkpoints/',
    checkpoint_file='checkpoint_best.pt',
    data_name_or_path='/root/fairseq/STS-B-bin'
)
```

```
roberta.cuda()
roberta.eval()
gold, pred = [], []
with open('/root/fairseq/glue_data/STS-B/dev.tsv') as fin:
    fin.readline()
    for index, line in enumerate(fin):
        tokens = line.strip().split('\t')
        sent1, sent2, target = tokens[7], tokens[8], float(tokens[9])
        tokens = roberta.encode(sent1, sent2)
        features = roberta.extract_features(tokens)
        predictions = 5.0 * roberta.model.classification_heads['sentence_classification_head'](features)
        gold.append(target)
        pred.append(predictions.item())

print('| Pearson: ', pearsonr(gold, pred))
```

```
sent1 = "Good morning"
sent2 = "Good morning"
tokens = roberta.encode(sent1, sent2)
features = roberta.extract_features(tokens)
predictions = 5.0 * roberta.model.classification_heads['sentence_classification_head'](features)
predictions
```
