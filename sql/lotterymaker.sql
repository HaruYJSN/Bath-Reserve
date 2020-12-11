CREATE TABLE lottery(userid VARCHAR(100), lott_num INT);
DECLARE @students INT;
SET @students = (SELECT count(*) FROM users WHERE userid not like 'test%');
DECLARE @i INT =0;
WHILE (@i < @students)
BEGIN
    INSERT INTO lottery VALUES('', @i);
    SET @i = @i + 1;
END