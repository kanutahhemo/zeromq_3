select sum(loss)/3+(select loss from loss_balance)/2 as available_balance from orders where is_active is false;
select loss as loss_balance from loss_balance;
select comment from groups where gid=(select min(gid) from orders where is_active is true);
select count(*) as oldest_orders_count from orders where gid=(select min(gid) from orders where is_active is true) and is_active is true;
select sum(loss) as oldest_orders_loss from orders where gid=(select min(gid) from orders where is_active is true) and is_active is true;
select sum(loss) as profit from orders where is_active is false;
select sum(loss) as current_loss from orders where is_active is true;
select (select sum(loss) as profit from orders where is_active is false) + (select sum(loss) as current_loss from orders where is_active is true);
select count(*) as count_orders from orders where is_active is true;
select count(*) as closed_orders from orders where is_active is false;
select sum(loss) as min_lass from orders where is_active is true group by gid order by 1 desc limit 1;
