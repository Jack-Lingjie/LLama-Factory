deepspeed --num_gpus 8 --num_nodes 8 --hostfile bash_script/config_files/hostfile \
src/train.py bash_script/glanchatv2_70B_debug_full_sft_2048_default_template_job.yaml --deepspeed examples/deepspeed/ds_z3_config.json

deepspeed --num_gpus 8 --num_nodes 8 --hostfile bash_script/config_files/hostfile \
src/train.py \
--model_name_or_path /mnt/lingjiejiang/textual_aesthetics/model_checkpoint/sft_merge_checkpoints/Meta-Llama-3.1-70B-Instruct \
--stage sft \
--do_train \
--finetuning_type full \
--flash_attn fa2 \
--dataset glanchat_v2 \
--template default \
--cutoff_len 2048 \
--overwrite_cache \
--preprocessing_num_workers 16 \
--output_dir /mnt/lingjiejiang/textual_aesthetics/exp/saves/glanchat_v2_70b_2048_default_template/fullft_lr5e6_e3_fx/sft \
--logging_steps 10 \
--save_steps 500 \
--plot_loss \
--overwrite_output_dir \
--per_device_train_batch_size 1 \
--gradient_accumulation_steps 8 \
--learning_rate 5.0e-6 \
--num_train_epochs 3.0 \
--lr_scheduler_type cosine \
--warmup_ratio 0.1 \
--bf16 \
--ddp_timeout 180000000 \
--val_size 0.1 \
--per_device_eval_batch_size 1 \
--eval_strategy steps \
--eval_steps 1000  \
--deepspeed examples/deepspeed/ds_z3_config.json



accelerate launch \
--config_file bash_script/config_files/deepspeed_config.yaml \
src/train.py bash_script/glanchatv2_70B_debug_full_sft_2048_default_template_job.yaml


deepspeed --num_gpus 8 --num_nodes 8 --hostfile bash_script/config_files/hostfile \
src/train.py bash_script/glanchatv2_70B_debug_full_sft_2048_default_template_job.yaml
# --deepspeed examples/deepspeed/ds_z3_config.json