import logging
import time


def run(
    *,
    channels,
    interval,
    enable_rclone,
    enable_vod_download=False,
    cleanup_uploaded_files=None,
    has_local_files=None,
    initialize,
    get_user_id,
    get_clips,
    download_clip,
    run_rclone,
    has_clip,
    save_clip,
    get_unuploaded_clips,
    mark_all_uploaded,
    get_videos=None,
    download_vod=None,
    has_vod=None,
    save_vod=None,
    get_unuploaded_vods=None,
    mark_all_vods_uploaded=None,
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
            else:
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

                        save_clip(
                            clip_id,
                            channel,
                            title,
                            clip["url"],
                            clip["created_at"],
                        )
                        logging.info("Saved clip: %s", clip_id)

                    except KeyboardInterrupt:
                        raise

                    except Exception:
                        logging.exception("Failed to process clip %s", clip_id)

            if enable_vod_download:
                videos = get_videos(uid)

                if not videos:
                    logging.info("No VODs returned")
                else:
                    logging.info(
                        "Fetched %d VODs for %s",
                        len(videos),
                        channel,
                    )

                    for video in videos:
                        vod_id = video["id"]
                        title = video["title"]

                        if has_vod(vod_id):
                            continue

                        logging.info(
                            "New VOD found for %s: %s",
                            channel,
                            title,
                        )

                        try:
                            success = download_vod(video, channel)

                            if not success:
                                logging.warning(
                                    "Skipping VOD because download failed: %s",
                                    vod_id,
                                )
                                continue

                            created_at = (
                                video.get("published_at")
                                or video.get("created_at")
                            )
                            save_vod(
                                vod_id,
                                channel,
                                title,
                                video["url"],
                                created_at,
                            )
                            logging.info("Saved VOD: %s", vod_id)

                        except KeyboardInterrupt:
                            raise

                        except Exception:
                            logging.exception(
                                "Failed to process VOD %s",
                                vod_id,
                            )

        if enable_rclone:
            pending_clips = get_unuploaded_clips()
            pending_vods = (
                get_unuploaded_vods()
                if enable_vod_download and get_unuploaded_vods
                else []
            )
            pending_uploads = len(pending_clips) + len(pending_vods)

            # also upload files left behind by an earlier run, so they
            # can be cleaned up even when nothing new was downloaded
            leftover_files = (
                not pending_uploads
                and cleanup_uploaded_files
                and has_local_files
                and has_local_files()
            )

            if pending_uploads or leftover_files:
                logging.info(
                    "%d items waiting for upload (%d clips, %d VODs)",
                    pending_uploads,
                    len(pending_clips),
                    len(pending_vods),
                )

                if run_rclone():
                    mark_all_uploaded()
                    if (
                        enable_vod_download
                        and mark_all_vods_uploaded
                        and pending_vods
                    ):
                        mark_all_vods_uploaded()
                    logging.info(
                        "Marked %d items as uploaded",
                        pending_uploads,
                    )

                    if cleanup_uploaded_files:
                        cleanup_uploaded_files()
                elif cleanup_uploaded_files:
                    logging.warning(
                        "Keeping local files because rclone upload failed"
                    )

        logging.info("Waiting %d seconds before next check", interval)
        sleep(interval)
