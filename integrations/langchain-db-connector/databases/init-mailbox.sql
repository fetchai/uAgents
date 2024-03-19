\c postgres;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_database WHERE datname = 'postgres'
    ) THEN
        CREATE DATABASE postgres;
    END IF;
END
$$;

\c postgres;

DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users (
    uid character varying(48) COLLATE pg_catalog."default" NOT NULL,
    registered_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    username text COLLATE pg_catalog."default",
    bytes_stored bigint NOT NULL DEFAULT 0,
    bytes_transferred bigint NOT NULL DEFAULT 0,
    plan_id character varying(120) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT users_pkey PRIMARY KEY (uid)
);


INSERT INTO public.users(
	uid, registered_at, username, bytes_stored, bytes_transferred, plan_id)
	VALUES ('user_1', CURRENT_TIMESTAMP, 0, 0, 0, 'default');



-- -- Table: public.mailboxes

DROP TABLE IF EXISTS public.mailboxes;

CREATE TABLE IF NOT EXISTS public.mailboxes
(
    address character varying(65) COLLATE pg_catalog."default" NOT NULL,
    name character varying(80) COLLATE pg_catalog."default" NOT NULL,
    registered_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    bytes_stored bigint NOT NULL DEFAULT 0,
    bytes_transferred bigint NOT NULL DEFAULT 0,
    owner_id character varying(48) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT mailboxes_pkey PRIMARY KEY (address)
)

TABLESPACE pg_default;


-- INSERT SCRIPTS

INSERT INTO public.mailboxes(
	address, name, registered_at, bytes_stored, bytes_transferred, owner_id)
	VALUES ('agent1q00k3au9pqwnr06s8aq6c9d6lvffe4g78rzz3wwy5jy6gyctdjr87gd90f7',  'My Super Cool Mailbox', CURRENT_TIMESTAMP, 0, 0, 'user_1');