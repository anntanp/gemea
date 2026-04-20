import sqlite3, os, time, gzip, multiprocessing, queue, sys
import httpx
import logging
import traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logging.getLogger("httpx").setLevel(logging.WARNING)

DB_PATH = os.environ.get("DB_PATH")
if DB_PATH is None:
    raise Exception("DB_PATH env variable is not defined, please set it")

DDB_URI = "https://api.deutsche-digitale-bibliothek.de/2/items/"
BUF_SIZE = int(os.environ.get("BUF_SIZE", 999))
SELECT_SIZE = int(os.environ.get("SELECT_SIZE", 50000))
WORKER_COUNT = int(os.environ.get("WORKER_COUNT", 8))
IMPORT_INTERVAL = int(os.environ.get("IMPORT_INTERVAL", 120))  # in seconds

OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "./out/")
if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)


def get_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """CREATE TABLE IF NOT EXISTS objs (uid TEXT PRIMARY KEY, download_timestamp TEXT, bufgz BLOB);
           CREATE TABLE IF NOT EXISTS srcs (uid TEXT PRIMARY KEY, download_timestamp TEXT, bufgz BLOB);
           PRAGMA journal_mode=WAL;"""
    )
    return db


def download_obj(uid, output_filepath):
    if os.path.exists(output_filepath):
        return True

    with httpx.Client() as client:
        try:
            uri = DDB_URI + uid
            resp = client.get(uri, follow_redirects=True, timeout=30.0)
            if resp.status_code == 200:
                open(output_filepath, "wb").write(gzip.compress(resp.content))
                return True
            else:
                logging.error(
                    f"Problem retrieving {uid} status code was {resp.status_code} {resp.text}"
                )
        except httpx.ConnectError:
            logging.error(f"Connect Error {uid}, sleeping a bit")
            time.sleep(1)
        except:
            logging.error(traceback.format_exc())
            logging.error(f"Problem with {uid}")


def worker(number, Q):
    while True:
        uid = Q.get()
        if uid is None:
            logging.info(f"Worker {number} 'None' received stopping.")
            break

        ok = download_obj(uid, os.path.join(OUTPUT_PATH, uid) + ".json.gz")
#        if ok:
#            ok = download_obj(f"{uid}/source/record", os.path.join(OUTPUT_PATH, uid) + ".xml.gz")
#        if not ok:
#            logging.info(f"Not OK on {uid}, stopping.")
            # break


def importer(Q):
    db = get_db()
    last_import = time.time()
    keep_going = True
    while not keep_going is None:
        try:
            keep_going = Q.get(timeout=IMPORT_INTERVAL)
            logging.info("Importer: None, received stopping.")
        except queue.Empty:
            pass
        logging.info("Importer: Gathering files")
        if time.time() - last_import > IMPORT_INTERVAL:
            added = []
            for filename in os.listdir(OUTPUT_PATH):
                filepath = os.path.join(OUTPUT_PATH, filename)
                file_contents = open(filepath, "rb").read()
                if filename.endswith(".xml.gz"):
                    table_name = "srcs"
                    uid = filename.replace(".xml.gz", "")
                elif filename.endswith(".json.gz"):
                    table_name = "objs"
                    uid = filename.replace(".json.gz", "")
                else:
                    continue
                timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.gmtime())
                db.execute(
                    f"UPDATE {table_name} SET download_timestamp = ?, bufgz = ? WHERE uid = ?",
                    (timestamp, file_contents, uid),
                )
                added.append(filepath)
            if len(added) > 0:
                logging.info(f"Committing {len(added)} to database")
                db.commit()
                for filepath in added:
                   os.remove(filepath)
            last_import = time.time()


def main():
    db = get_db()
    if len(sys.argv) > 1 and sys.argv[1] == "import":
        filename = sys.argv[2]
        ids = [(line.strip(),) for line in open(filename).readlines()]
        print(f"Read {len(ids)} now inserting for fresh download")
        db.executemany("INSERT OR IGNORE INTO srcs VALUES (?, null, null)", ids)
        db.executemany("INSERT OR IGNORE INTO objs VALUES (?, null, null)", ids)
        db.commit()
        print("Done")

        sys.exit()

    Q = multiprocessing.Queue()
    QI = multiprocessing.Queue()
    workers = []
    for w in range(WORKER_COUNT):
        wp = multiprocessing.Process(target=worker, daemon=True, args=(w, Q))
        wp.start()
        workers.append(wp)
    importer_p = multiprocessing.Process(target=importer, daemon=True, args=(QI,))
    importer_p.start()

    keep_going = True
    while keep_going:
        uids = [
            uid
            for uid, _ in db.execute(
                f"SELECT uid, download_timestamp FROM objs WHERE bufgz IS NULL LIMIT {SELECT_SIZE}"
            )
        ]
        if len(uids) < 1:
            keep_going = False
        for uid in uids:
            Q.put(uid)
        time.sleep(IMPORT_INTERVAL * 2)
        logging.info(f"Batch of {len(uids)} queued, getting new ones")

    logging.info("Done with Q, waiting for workers to finish")
    for w in range(WORKER_COUNT):
        Q.put(None)
    for w in workers:
        w.join()
    QI.put(None)


if __name__ == "__main__":
    main()
