import logging
import time


def run(
    *,
    channels,
    interval,
    enable_rclone,
    initialize,
    get_user_id,
    get_clips,
    download_clip,
    run_rclone,
    has_clip,
    save_clip,
    get_unuploaded_clips,
    mark_all_uploaded,
    sleep=time.sleep,
):
    logging.info("Bot started...")

    initialize()
    user_ids = {}

    for channel in channels:
        logging.info("Resolving user: %s", channel)
        uid = get_user_id(channel)
        if uid:
            user_ids[channel] = uid
            logging.info("Resolved user ID: %s", uid)

    while True:
        for channel, uid in user_ids.items():
            logging.info("Checking channel: %s (%s)", channel, uid)

            clips = get_clips(uid)

            if not clips:
                logging.info("No clips returned")
                continue

            logging.info("Fetched %d clips for %s", len(clips), channel)

            for clip in clips:
                clip_id = clip["id"]
                title = clip["title"]

                if has_clip(clip_id):
                    continue

                logging.info("New clip found for %s: %s", channel, title)

                try:
                    success = download_clip(clip, channel)

                    if not success:
                        logging.warning(
                            "Skipping clip because download failed: %s",
                            clip_id,
                        )
                        continue

                    save_clip(clip_id, channel, title, clip["url"])
                    logging.info("Saved clip: %s", clip_id)

                except KeyboardInterrupt:
                    raise

                except Exception:
                    logging.exception("Failed to process clip %s", clip_id)

        if enable_rclone:
            pending_uploads = get_unuploaded_clips()

            if pending_uploads:
                logging.info(
                    "%d clips waiting for upload",
                    len(pending_uploads),
                )

                if run_rclone():
                    mark_all_uploaded()
                    logging.info(
                        "Marked %d clips as uploaded",
                        len(pending_uploads),
                    )

        logging.info("Waiting %d seconds before next check", interval)
        sleep(interval)
