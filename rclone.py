import logging


def run_rclone(
    *,
    enable_rclone,
    rclone_remotes,
    rclone_destination,
    rclone_command,
    rclone_args,
    rclone_show_progress,
    subprocess_module,
):
    if not enable_rclone:
        return True

    overall_success = True

    logging.info(
        "Starting rclone %s → %s",
        rclone_command,
        rclone_remotes,
    )

    for remote in rclone_remotes:
        destination = f"{remote}:{rclone_destination}"

        cmd = [
            "rclone",
            rclone_command,
            "clips",
            destination,
        ]

        if rclone_show_progress:
            cmd.append("--progress")

        cmd.extend(rclone_args)

        logging.info("RCLONE - Uploading clips → %s", destination)

        try:
            if rclone_show_progress:
                stdout = None
                stderr = None
            else:
                stdout = subprocess_module.DEVNULL
                stderr = subprocess_module.DEVNULL

            result = subprocess_module.run(cmd, stdout=stdout, stderr=stderr)

            if result.returncode == 0:
                logging.info("rclone completed successfully → %s", destination)
            else:
                logging.error(
                    "rclone failed for %s with exit code: %d",
                    destination,
                    result.returncode,
                )
                overall_success = False

        except FileNotFoundError:
            logging.error(
                "rclone was not found. Install rclone or disable enable_rclone."
            )
            return False

        except Exception:
            logging.exception(
                "Unexpected error while running rclone for %s",
                destination,
            )
            overall_success = False

    return overall_success
